"""Panel del artista: obras, imagenes y consultas (requiere access token)."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile

from app.api.deps import CurrentArtist, SessionDep, get_current_artist
from app.core.config import get_settings
from app.core.storage import ObjectStorage, get_storage
from app.models import ArtworkStatus, Inquiry, InquiryStatus
from app.schemas.artwork import (
    ArtworkCreate,
    ArtworkDetail,
    ArtworkImageRead,
    ArtworkListItem,
    ArtworkUpdate,
)
from app.schemas.common import Page, PaginationParams
from app.schemas.inquiry import InquiryRead, InquiryStatusUpdate
from app.services import artwork_service, inquiry_service

router = APIRouter(prefix="/panel", tags=["panel"], dependencies=[Depends(get_current_artist)])

StorageDep = Annotated[ObjectStorage, Depends(get_storage)]
Pagination = Annotated[PaginationParams, Depends()]


def _inquiry_read(inquiry: Inquiry) -> InquiryRead:
    assert inquiry.id is not None  # noqa: S101
    return InquiryRead(
        id=inquiry.id,
        artwork_id=inquiry.artwork_id,
        artwork_title=inquiry.artwork_title,
        name=inquiry.name,
        email=inquiry.email,
        phone=inquiry.phone,
        message=inquiry.message,
        status=inquiry.status,
        created_at=inquiry.created_at,
    )


# ─── Obras ──────────────────────────────────────────────────────────────────────


@router.get("/artworks", response_model=Page[ArtworkListItem], summary="Mis obras (todas)")
def list_my_artworks(
    artist: CurrentArtist,
    session: SessionDep,
    pagination: Pagination,
    status: Annotated[ArtworkStatus | None, Query()] = None,
) -> Page[ArtworkListItem]:
    assert artist.id is not None  # noqa: S101
    artworks, total = artwork_service.list_for_artist(session, artist.id, pagination, status)
    return Page.build(artwork_service.to_list_items(session, artworks), total, pagination)


@router.post(
    "/artworks",
    response_model=ArtworkDetail,
    status_code=201,
    summary="Crear obra",
    description="Errores: 409 si se crea ya publicada (una obra nueva no tiene imagenes).",
)
def create_artwork(
    body: ArtworkCreate, artist: CurrentArtist, session: SessionDep
) -> ArtworkDetail:
    assert artist.id is not None  # noqa: S101
    artwork = artwork_service.create_artwork(session, artist.id, body)
    return artwork_service.to_detail(session, artwork)


@router.get("/artworks/{artwork_id}", response_model=ArtworkDetail, summary="Detalle de mi obra")
def get_my_artwork(artwork_id: int, artist: CurrentArtist, session: SessionDep) -> ArtworkDetail:
    assert artist.id is not None  # noqa: S101
    artwork = artwork_service.get_owned(session, artist.id, artwork_id)
    return artwork_service.to_detail(session, artwork)


@router.patch(
    "/artworks/{artwork_id}",
    response_model=ArtworkDetail,
    summary="Editar obra (parcial)",
    description="Errores: 404 obra ajena o inexistente, 409 publicar sin imagenes.",
)
def update_my_artwork(
    artwork_id: int, body: ArtworkUpdate, artist: CurrentArtist, session: SessionDep
) -> ArtworkDetail:
    assert artist.id is not None  # noqa: S101
    artwork = artwork_service.get_owned(session, artist.id, artwork_id)
    artwork = artwork_service.update_artwork(session, artwork, body)
    return artwork_service.to_detail(session, artwork)


@router.delete("/artworks/{artwork_id}", status_code=204, summary="Borrar obra")
def delete_my_artwork(
    artwork_id: int, artist: CurrentArtist, session: SessionDep, storage: StorageDep
) -> Response:
    assert artist.id is not None  # noqa: S101
    artwork = artwork_service.get_owned(session, artist.id, artwork_id)
    artwork_service.delete_artwork(session, storage, artwork)
    return Response(status_code=204)


# ─── Imagenes ───────────────────────────────────────────────────────────────────


@router.post(
    "/artworks/{artwork_id}/images",
    response_model=ArtworkImageRead,
    status_code=201,
    summary="Subir imagen de una obra",
    description="multipart/form-data con `file` (JPEG/PNG/WebP) y `alt_text` opcional. "
    "Se valida el contenido real, se elimina EXIF y se guardan WebP + miniatura en MinIO. "
    "Errores: 413 demasiado grande, 415 formato no admitido, 422 imagen invalida, "
    "409 limite de imagenes.",
)
def upload_image(
    artwork_id: int,
    artist: CurrentArtist,
    session: SessionDep,
    storage: StorageDep,
    file: Annotated[UploadFile, File(description="Imagen JPEG, PNG o WebP")],
    alt_text: Annotated[str | None, Form(max_length=200)] = None,
) -> ArtworkImageRead:
    assert artist.id is not None  # noqa: S101
    artwork = artwork_service.get_owned(session, artist.id, artwork_id)
    max_bytes = get_settings().max_upload_bytes
    # Se lee un byte de mas para detectar el exceso sin cargar archivos enormes en memoria
    data = file.file.read(max_bytes + 1)
    image = artwork_service.add_image(session, storage, artwork, data, file.content_type, alt_text)
    return artwork_service.image_read(image)


@router.delete("/artworks/{artwork_id}/images/{image_id}", status_code=204, summary="Borrar imagen")
def delete_image(
    artwork_id: int,
    image_id: int,
    artist: CurrentArtist,
    session: SessionDep,
    storage: StorageDep,
) -> Response:
    assert artist.id is not None  # noqa: S101
    artwork = artwork_service.get_owned(session, artist.id, artwork_id)
    artwork_service.delete_image(session, storage, artwork, image_id)
    return Response(status_code=204)


# ─── Consultas ──────────────────────────────────────────────────────────────────


@router.get("/inquiries", response_model=Page[InquiryRead], summary="Mis consultas")
def list_my_inquiries(
    artist: CurrentArtist,
    session: SessionDep,
    pagination: Pagination,
    status: Annotated[InquiryStatus | None, Query()] = None,
    artwork_id: Annotated[int | None, Query(ge=1)] = None,
) -> Page[InquiryRead]:
    assert artist.id is not None  # noqa: S101
    inquiries, total = inquiry_service.list_inquiries(
        session, artist.id, pagination, status, artwork_id
    )
    return Page.build([_inquiry_read(inquiry) for inquiry in inquiries], total, pagination)


@router.patch(
    "/inquiries/{inquiry_id}",
    response_model=InquiryRead,
    summary="Cambiar el estado de una consulta",
    description="Errores: 404 consulta ajena o inexistente.",
)
def update_inquiry_status(
    inquiry_id: int, body: InquiryStatusUpdate, artist: CurrentArtist, session: SessionDep
) -> InquiryRead:
    assert artist.id is not None  # noqa: S101
    inquiry = inquiry_service.update_status(session, artist.id, inquiry_id, body.status)
    return _inquiry_read(inquiry)
