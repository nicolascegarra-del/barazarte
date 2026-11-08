"""Logica de negocio de obras e imagenes (publico y panel del artista)."""

import logging
import uuid
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, update
from sqlmodel import Session, col, select

from app.core.config import get_settings
from app.core.errors import AppError, not_found
from app.core.storage import ObjectStorage, public_url
from app.models import (
    PUBLIC_ARTWORK_STATUSES,
    Artist,
    Artwork,
    ArtworkImage,
    ArtworkStatus,
    Inquiry,
)
from app.models.base import utcnow
from app.schemas.artist import ArtistSummary
from app.schemas.artwork import (
    ArtworkCreate,
    ArtworkDetail,
    ArtworkImageRead,
    ArtworkListItem,
    ArtworkUpdate,
)
from app.schemas.common import PaginationParams
from app.services.image_service import process_image

logger = logging.getLogger(__name__)

_NULLABLE_FIELDS = {"depth_cm", "price", "description"}


# ─── Serializacion (consultas por lotes: sin N+1) ───────────────────────────────


def _images_by_artwork(
    session: Session, artwork_ids: Sequence[int]
) -> dict[int, list[ArtworkImage]]:
    grouped: dict[int, list[ArtworkImage]] = defaultdict(list)
    if not artwork_ids:
        return grouped
    statement = (
        select(ArtworkImage)
        .where(col(ArtworkImage.artwork_id).in_(artwork_ids))
        .order_by(col(ArtworkImage.position), col(ArtworkImage.id))
    )
    for image in session.exec(statement):
        grouped[image.artwork_id].append(image)
    return grouped


def _artists_by_id(session: Session, artist_ids: set[int]) -> dict[int, Artist]:
    if not artist_ids:
        return {}
    statement = select(Artist).where(col(Artist.id).in_(artist_ids))
    return {artist.id: artist for artist in session.exec(statement) if artist.id is not None}


def _image_read(image: ArtworkImage) -> ArtworkImageRead:
    assert image.id is not None  # noqa: S101 - la fila ya esta persistida
    return ArtworkImageRead(
        id=image.id,
        url=public_url(image.storage_key),
        thumb_url=public_url(image.thumb_key),
        alt_text=image.alt_text,
        position=image.position,
        width=image.width,
        height=image.height,
    )


def _artist_summary(artist: Artist) -> ArtistSummary:
    assert artist.id is not None  # noqa: S101
    return ArtistSummary(id=artist.id, display_name=artist.display_name)


def to_list_items(session: Session, artworks: Sequence[Artwork]) -> list[ArtworkListItem]:
    ids = [artwork.id for artwork in artworks if artwork.id is not None]
    images = _images_by_artwork(session, ids)
    artists = _artists_by_id(session, {artwork.artist_id for artwork in artworks})
    items = []
    for artwork in artworks:
        assert artwork.id is not None  # noqa: S101
        cover = images[artwork.id][0] if images[artwork.id] else None
        items.append(
            ArtworkListItem(
                id=artwork.id,
                title=artwork.title,
                technique=artwork.technique,
                width_cm=artwork.width_cm,
                height_cm=artwork.height_cm,
                year=artwork.year,
                price=artwork.price,
                status=artwork.status,
                artist=_artist_summary(artists[artwork.artist_id]),
                cover_thumb_url=public_url(cover.thumb_key) if cover else None,
            )
        )
    return items


def to_detail(session: Session, artwork: Artwork) -> ArtworkDetail:
    assert artwork.id is not None  # noqa: S101
    images = _images_by_artwork(session, [artwork.id])[artwork.id]
    artist = session.get(Artist, artwork.artist_id)
    assert artist is not None  # noqa: S101 - FK garantiza su existencia
    return ArtworkDetail(
        id=artwork.id,
        title=artwork.title,
        technique=artwork.technique,
        width_cm=artwork.width_cm,
        height_cm=artwork.height_cm,
        depth_cm=artwork.depth_cm,
        year=artwork.year,
        price=artwork.price,
        description=artwork.description,
        status=artwork.status,
        artist=_artist_summary(artist),
        images=[_image_read(image) for image in images],
        created_at=artwork.created_at,
        updated_at=artwork.updated_at,
    )


# ─── Consultas ──────────────────────────────────────────────────────────────────


def _paginate(
    session: Session, conditions: list[Any], params: PaginationParams
) -> tuple[list[Artwork], int]:
    total = session.exec(select(func.count()).select_from(Artwork).where(*conditions)).one()
    statement = (
        select(Artwork)
        .where(*conditions)
        .order_by(col(Artwork.created_at).desc(), col(Artwork.id).desc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    return list(session.exec(statement)), total


def list_public(
    session: Session,
    params: PaginationParams,
    artist_id: int | None,
    status: ArtworkStatus | None,
) -> tuple[list[Artwork], int]:
    conditions: list[Any] = [col(Artwork.status).in_(PUBLIC_ARTWORK_STATUSES)]
    if status is not None:
        conditions.append(Artwork.status == status)
    if artist_id is not None:
        conditions.append(Artwork.artist_id == artist_id)
    return _paginate(session, conditions, params)


def get_public(session: Session, artwork_id: int) -> Artwork:
    artwork = session.get(Artwork, artwork_id)
    if artwork is None or artwork.status not in PUBLIC_ARTWORK_STATUSES:
        raise not_found("Obra no encontrada.")
    return artwork


def list_for_artist(
    session: Session, artist_id: int, params: PaginationParams, status: ArtworkStatus | None
) -> tuple[list[Artwork], int]:
    conditions: list[Any] = [Artwork.artist_id == artist_id]
    if status is not None:
        conditions.append(Artwork.status == status)
    return _paginate(session, conditions, params)


def get_owned(session: Session, artist_id: int, artwork_id: int) -> Artwork:
    """Devuelve 404 (no 403) para obras ajenas: no se revela que existen."""
    artwork = session.get(Artwork, artwork_id)
    if artwork is None or artwork.artist_id != artist_id:
        raise not_found("Obra no encontrada.")
    return artwork


def _image_count(session: Session, artwork_id: int) -> int:
    statement = (
        select(func.count()).select_from(ArtworkImage).where(ArtworkImage.artwork_id == artwork_id)
    )
    return session.exec(statement).one()


def _ensure_can_be_public(session: Session, artwork_id: int | None, status: ArtworkStatus) -> None:
    if status not in PUBLIC_ARTWORK_STATUSES:
        return
    if artwork_id is None or _image_count(session, artwork_id) == 0:
        raise AppError(
            409,
            "ARTWORK_NEEDS_IMAGE",
            "La obra necesita al menos una imagen para publicarse.",
            field="status",
        )


# ─── Escritura ──────────────────────────────────────────────────────────────────


def create_artwork(session: Session, artist_id: int, data: ArtworkCreate) -> Artwork:
    _ensure_can_be_public(session, None, data.status)
    artwork = Artwork(artist_id=artist_id, **data.model_dump())
    session.add(artwork)
    session.commit()
    session.refresh(artwork)
    return artwork


def update_artwork(session: Session, artwork: Artwork, data: ArtworkUpdate) -> Artwork:
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if value is None and field not in _NULLABLE_FIELDS:
            raise AppError(422, "VALIDATION_ERROR", "Este campo no puede ser nulo.", field=field)
    new_status = changes.get("status", artwork.status)
    _ensure_can_be_public(session, artwork.id, new_status)
    for field, value in changes.items():
        setattr(artwork, field, value)
    artwork.updated_at = utcnow()
    session.add(artwork)
    session.commit()
    session.refresh(artwork)
    return artwork


def delete_artwork(session: Session, storage: ObjectStorage, artwork: Artwork) -> None:
    assert artwork.id is not None  # noqa: S101
    images = list(session.exec(select(ArtworkImage).where(ArtworkImage.artwork_id == artwork.id)))
    keys = [key for image in images for key in (image.storage_key, image.thumb_key)]
    # Las consultas se conservan (historial del artista) pero pierden el vinculo a la obra
    session.exec(  # type: ignore[call-overload]
        update(Inquiry).where(col(Inquiry.artwork_id) == artwork.id).values(artwork_id=None)
    )
    for image in images:
        session.delete(image)
    session.delete(artwork)
    session.commit()
    _delete_objects(storage, keys)


def _delete_objects(storage: ObjectStorage, keys: Sequence[str]) -> None:
    """Borrado best-effort: un objeto huerfano en MinIO no debe romper la operacion de BD."""
    for key in keys:
        try:
            storage.delete(key)
        except Exception:
            logger.exception("No se pudo borrar el objeto %s de MinIO", key)


def add_image(
    session: Session,
    storage: ObjectStorage,
    artwork: Artwork,
    data: bytes,
    content_type: str | None,
    alt_text: str | None,
) -> ArtworkImage:
    assert artwork.id is not None  # noqa: S101
    settings = get_settings()
    if _image_count(session, artwork.id) >= settings.max_images_per_artwork:
        raise AppError(
            409,
            "IMAGE_LIMIT_REACHED",
            f"Maximo {settings.max_images_per_artwork} imagenes por obra.",
        )
    processed = process_image(data, content_type, settings.max_upload_bytes)

    base_key = f"artworks/{artwork.id}/{uuid.uuid4().hex}"
    main_key, thumb_key = f"{base_key}.webp", f"{base_key}_thumb.webp"
    storage.put(main_key, processed.main, "image/webp")
    storage.put(thumb_key, processed.thumb, "image/webp")

    max_position = session.exec(
        select(func.max(ArtworkImage.position)).where(ArtworkImage.artwork_id == artwork.id)
    ).one()
    image = ArtworkImage(
        artwork_id=artwork.id,
        storage_key=main_key,
        thumb_key=thumb_key,
        alt_text=alt_text or None,
        position=(max_position + 1) if max_position is not None else 0,
        width=processed.width,
        height=processed.height,
    )
    try:
        session.add(image)
        session.commit()
    except Exception:
        session.rollback()
        _delete_objects(storage, [main_key, thumb_key])
        raise
    session.refresh(image)
    return image


def delete_image(session: Session, storage: ObjectStorage, artwork: Artwork, image_id: int) -> None:
    image = session.get(ArtworkImage, image_id)
    if image is None or image.artwork_id != artwork.id:
        raise not_found("Imagen no encontrada.")
    assert artwork.id is not None  # noqa: S101
    if artwork.status in PUBLIC_ARTWORK_STATUSES and _image_count(session, artwork.id) <= 1:
        raise AppError(
            409,
            "ARTWORK_NEEDS_IMAGE",
            "No se puede borrar la ultima imagen de una obra publicada.",
        )
    keys = [image.storage_key, image.thumb_key]
    session.delete(image)
    session.commit()
    _delete_objects(storage, keys)


def image_read(image: ArtworkImage) -> ArtworkImageRead:
    return _image_read(image)
