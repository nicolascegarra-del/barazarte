"""Endpoints publicos de la galeria (sin autenticacion)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import SessionDep
from app.core.config import get_settings
from app.core.errors import not_found
from app.core.rate_limit import rate_limit
from app.models import Artist, ArtworkStatus
from app.schemas.artist import ArtistPublic
from app.schemas.artwork import ArtworkDetail, ArtworkListItem, PublicStatus
from app.schemas.common import Page, PaginationParams
from app.schemas.inquiry import InquiryAccepted, InquiryCreate
from app.services import artwork_service, inquiry_service

router = APIRouter(tags=["public"])


def _inquiry_limits() -> tuple[int, int]:
    settings = get_settings()
    return settings.inquiry_rate_limit, settings.inquiry_rate_window_seconds


@router.get(
    "/artworks",
    response_model=Page[ArtworkListItem],
    summary="Listado paginado de obras",
    description="Solo obras publicadas, reservadas o vendidas (nunca borradores), "
    "de la mas reciente a la mas antigua.",
)
def list_artworks(
    session: SessionDep,
    pagination: Annotated[PaginationParams, Depends()],
    artist_id: Annotated[int | None, Query(ge=1)] = None,
    status: Annotated[PublicStatus | None, Query()] = None,
) -> Page[ArtworkListItem]:
    artworks, total = artwork_service.list_public(
        session, pagination, artist_id, ArtworkStatus(status) if status else None
    )
    return Page.build(artwork_service.to_list_items(session, artworks), total, pagination)


@router.get(
    "/artworks/{artwork_id}",
    response_model=ArtworkDetail,
    summary="Detalle de una obra",
    description="Errores: 404 si no existe o es un borrador.",
)
def get_artwork(artwork_id: int, session: SessionDep) -> ArtworkDetail:
    artwork = artwork_service.get_public(session, artwork_id)
    return artwork_service.to_detail(session, artwork)


@router.get(
    "/artists/{artist_id}",
    response_model=ArtistPublic,
    summary="Perfil publico de un artista",
    description="No expone el email. Errores: 404 si no existe o esta inactivo.",
)
def get_artist(artist_id: int, session: SessionDep) -> ArtistPublic:
    artist = session.get(Artist, artist_id)
    if artist is None or not artist.is_active:
        raise not_found("Artista no encontrado.")
    return ArtistPublic(
        id=artist_id, display_name=artist.display_name, bio=artist.bio, website=artist.website
    )


@router.post(
    "/artworks/{artwork_id}/inquiries",
    response_model=InquiryAccepted,
    status_code=202,
    summary="Enviar una consulta sobre una obra",
    description="Guarda la consulta y encola los emails al artista y al comprador. "
    "Protegido con honeypot (campo `website`) y rate limit por IP. "
    "Errores: 404 obra no disponible, 422 validacion, 429 demasiadas consultas.",
    dependencies=[Depends(rate_limit("inquiry", _inquiry_limits))],
)
def create_inquiry(
    artwork_id: int, body: InquiryCreate, session: SessionDep, request: Request
) -> InquiryAccepted:
    if body.website.strip():
        # Un bot rellenó el honeypot: respuesta identica a la real, pero sin guardar ni enviar
        return InquiryAccepted()
    inquiry_service.create_inquiry(session, artwork_id, body)
    return InquiryAccepted()
