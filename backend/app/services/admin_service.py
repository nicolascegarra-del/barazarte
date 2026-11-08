"""Panel de administracion: estadisticas globales y gestion de artistas."""

from datetime import timedelta
from typing import Any

from sqlalchemy import case, func
from sqlmodel import Session, col, select

from app.core.errors import AppError, forbidden, not_found
from app.models import Artist, Artwork, ArtworkStatus, Inquiry, InquiryStatus, VisitDaily
from app.models.base import utcnow
from app.schemas.admin import (
    AdminArtistRead,
    AdminArtistUpdate,
    AdminStats,
    ArtistStats,
    ArtworkStats,
    InquiryStats,
    VisitDay,
    VisitStats,
)
from app.schemas.common import PaginationParams
from app.services.visit_service import today_utc

STATS_DAYS = 30


def _count_by(session: Session, column: Any) -> dict[Any, int]:
    rows = session.exec(select(column, func.count()).group_by(column))
    return {row[0]: row[1] for row in rows}


def _artist_stats(session: Session) -> ArtistStats:
    total, active, unverified = session.exec(
        select(
            func.count(),
            func.coalesce(func.sum(case((col(Artist.is_active).is_(True), 1), else_=0)), 0),
            func.coalesce(func.sum(case((col(Artist.email_verified).is_(False), 1), else_=0)), 0),
        )
    ).one()
    return ArtistStats(
        total=total, active=int(active), disabled=total - int(active), unverified=int(unverified)
    )


def _visit_stats(session: Session) -> VisitStats:
    since = today_utc() - timedelta(days=STATS_DAYS - 1)
    total = session.exec(select(func.coalesce(func.sum(VisitDaily.count), 0))).one()
    rows = session.exec(
        select(VisitDaily.date, func.sum(VisitDaily.count))
        .where(VisitDaily.date >= since)
        .group_by(VisitDaily.date)
    )
    per_day = {day: int(count) for day, count in rows}
    days = [since + timedelta(days=offset) for offset in range(STATS_DAYS)]
    by_day = [VisitDay(date=day.isoformat(), count=per_day.get(day, 0)) for day in days]
    return VisitStats(
        total=int(total), last_30_days=sum(item.count for item in by_day), by_day=by_day
    )


def get_stats(session: Session) -> AdminStats:
    artwork_counts = _count_by(session, Artwork.status)
    inquiry_counts = _count_by(session, Inquiry.status)
    return AdminStats(
        artists=_artist_stats(session),
        artworks=ArtworkStats(
            total=sum(artwork_counts.values()),
            borrador=artwork_counts.get(ArtworkStatus.DRAFT, 0),
            publicado=artwork_counts.get(ArtworkStatus.PUBLISHED, 0),
            reservado=artwork_counts.get(ArtworkStatus.RESERVED, 0),
            vendido=artwork_counts.get(ArtworkStatus.SOLD, 0),
        ),
        inquiries=InquiryStats(
            total=sum(inquiry_counts.values()),
            nueva=inquiry_counts.get(InquiryStatus.NEW, 0),
            contactado=inquiry_counts.get(InquiryStatus.CONTACTED, 0),
            vendida=inquiry_counts.get(InquiryStatus.SOLD, 0),
        ),
        visits=_visit_stats(session),
    )


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _aggregate_columns(artist_id: Any) -> tuple[Any, Any, Any, Any]:
    """Subqueries escalares (artworks, publicadas, consultas, visitas) de un artista.
    Correlacionadas con la fila de Artist: todo en una unica consulta, sin N+1."""
    artworks_count = select(func.count()).where(Artwork.artist_id == artist_id).scalar_subquery()
    published_count = (
        select(func.count())
        .where(Artwork.artist_id == artist_id, Artwork.status == ArtworkStatus.PUBLISHED)
        .scalar_subquery()
    )
    inquiries_count = select(func.count()).where(Inquiry.artist_id == artist_id).scalar_subquery()
    visits_count = (
        select(func.coalesce(func.sum(VisitDaily.count), 0))
        .where(
            col(VisitDaily.artwork_id).in_(select(Artwork.id).where(Artwork.artist_id == artist_id))
        )
        .scalar_subquery()
    )
    return artworks_count, published_count, inquiries_count, visits_count


def list_artists(
    session: Session, params: PaginationParams, query: str | None
) -> tuple[list[AdminArtistRead], int]:
    conditions: list[Any] = []
    if query and query.strip():
        pattern = f"%{_escape_like(query.strip())}%"
        conditions.append(
            col(Artist.display_name).ilike(pattern, escape="\\")
            | col(Artist.email).ilike(pattern, escape="\\")
        )
    total = session.exec(select(func.count()).select_from(Artist).where(*conditions)).one()
    statement = (
        select(Artist, *_aggregate_columns(Artist.id))
        .where(*conditions)
        .order_by(col(Artist.created_at).desc(), col(Artist.id).desc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    items = [
        _admin_read(artist, artworks, published, inquiries, int(visits))
        for artist, artworks, published, inquiries, visits in session.exec(statement)
    ]
    return items, total


def _admin_read(
    artist: Artist, artworks: int, published: int, inquiries: int, visits: int
) -> AdminArtistRead:
    assert artist.id is not None  # noqa: S101
    return AdminArtistRead(
        id=artist.id,
        email=artist.email,
        display_name=artist.display_name,
        is_active=artist.is_active,
        email_verified=artist.email_verified,
        is_admin=artist.is_admin,
        max_artworks=artist.max_artworks,
        artworks_count=artworks,
        published_count=published,
        inquiries_count=inquiries,
        visits_count=visits,
        created_at=artist.created_at,
    )


def _get_manageable(session: Session, admin: Artist, artist_id: int) -> Artist:
    artist = session.get(Artist, artist_id)
    if artist is None:
        raise not_found("Artista no encontrado.")
    if artist.is_admin and artist.id != admin.id:
        raise forbidden("No puedes modificar a otro administrador.")
    return artist


def update_artist(
    session: Session, admin: Artist, artist_id: int, data: AdminArtistUpdate
) -> AdminArtistRead:
    artist = _get_manageable(session, admin, artist_id)
    # model_fields_set distingue "ausente" (sin cambio) de null (ilimitado)
    changes = data.model_dump(exclude_unset=True)
    if "is_active" in changes:
        if changes["is_active"] is None:
            raise AppError(422, "VALIDATION_ERROR", "Este campo no puede ser nulo.", "is_active")
        if artist.id == admin.id and not changes["is_active"]:
            raise AppError(409, "CANNOT_DISABLE_SELF", "No puedes desactivar tu propia cuenta.")
        artist.is_active = changes["is_active"]
    if "max_artworks" in changes:
        artist.max_artworks = changes["max_artworks"]
    artist.updated_at = utcnow()
    session.add(artist)
    session.commit()
    session.refresh(artist)
    counts = session.exec(select(*_aggregate_columns(artist.id))).one()
    return _admin_read(artist, counts[0], counts[1], counts[2], int(counts[3]))


def get_artist_for_reset(session: Session, admin: Artist, artist_id: int) -> Artist:
    artist = _get_manageable(session, admin, artist_id)
    if not artist.is_active:
        raise AppError(
            409, "ACCOUNT_DISABLED", "La cuenta esta desactivada; reactivala antes de enviar."
        )
    return artist
