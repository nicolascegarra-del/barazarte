"""Endpoints publicos de la galeria (sin autenticacion)."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response

from app.api.deps import SessionDep
from app.core.config import get_settings
from app.core.errors import not_found
from app.core.rate_limit import rate_limit
from app.core.storage import ObjectStorage, get_storage
from app.models import Artist, ArtworkStatus
from app.schemas.admin import TrackRequest
from app.schemas.artist import ArtistPublic
from app.schemas.artwork import ArtworkDetail, ArtworkListItem, PublicStatus
from app.schemas.catalog import ArtworkFacets, ArtworkNeighbors, ArtworkSize, ArtworkSort
from app.schemas.common import Page, PaginationParams
from app.schemas.inquiry import InquiryAccepted, InquiryCreate
from app.schemas.push import PushPublicKey
from app.services import artwork_service, inquiry_service, og_image_service, visit_service

router = APIRouter(tags=["public"])

StorageDep = Annotated[ObjectStorage, Depends(get_storage)]


def _inquiry_limits() -> tuple[int, int]:
    settings = get_settings()
    return settings.inquiry_rate_limit, settings.inquiry_rate_window_seconds


def _track_limits() -> tuple[int, int]:
    settings = get_settings()
    return settings.track_rate_limit, settings.track_rate_window_seconds


@router.get(
    "/artworks",
    response_model=Page[ArtworkListItem],
    summary="Listado paginado y filtrable de obras",
    description="Solo obras publicadas, reservadas o vendidas (nunca borradores) de artistas "
    "activos. Los filtros se combinan con AND. `min_price`/`max_price` excluyen las obras sin "
    "precio. `size` usa el lado mayor: pequeno < 50 cm, mediano 50-100 cm, grande > 100 cm. "
    "`available=true` deja solo las publicadas. Orden por defecto: mas recientes; con "
    "`precio_asc`/`precio_desc` las obras sin precio van al final. "
    "Errores: 422 si algun parametro es invalido.",
)
def list_artworks(
    session: SessionDep,
    pagination: Annotated[PaginationParams, Depends()],
    artist_id: Annotated[int | None, Query(ge=1)] = None,
    status: Annotated[PublicStatus | None, Query()] = None,
    technique: Annotated[
        str | None, Query(min_length=1, max_length=120, description="Tecnica exacta")
    ] = None,
    min_price: Annotated[Decimal | None, Query(ge=0, max_digits=10, decimal_places=2)] = None,
    max_price: Annotated[Decimal | None, Query(ge=0, max_digits=10, decimal_places=2)] = None,
    size: Annotated[ArtworkSize | None, Query()] = None,
    available: Annotated[bool | None, Query()] = None,
    sort: Annotated[ArtworkSort, Query()] = "recientes",
) -> Page[ArtworkListItem]:
    filters = artwork_service.PublicArtworkFilters(
        artist_id=artist_id,
        status=ArtworkStatus(status) if status else None,
        technique=technique,
        min_price=min_price,
        max_price=max_price,
        size=size,
        available=available,
        sort=sort,
    )
    artworks, total = artwork_service.list_public(session, pagination, filters)
    return Page.build(artwork_service.to_list_items(session, artworks), total, pagination)


@router.get(
    "/artworks/facets",
    response_model=ArtworkFacets,
    summary="Facetas del catalogo",
    description="Conteos por tecnica y artista y rango de precios sobre todas las obras "
    "visibles, sin filtros.",
)
def get_artwork_facets(session: SessionDep) -> ArtworkFacets:
    return artwork_service.get_facets(session)


@router.get(
    "/artworks/{artwork_id}/neighbors",
    response_model=ArtworkNeighbors,
    summary="Obras anterior y siguiente",
    description="Segun el orden `recientes` del listado publico. "
    "Errores: 404 si la obra no es visible.",
)
def get_artwork_neighbors(artwork_id: int, session: SessionDep) -> ArtworkNeighbors:
    return artwork_service.get_neighbors(session, artwork_id)


@router.get(
    "/artworks/{artwork_id}/og.jpg",
    summary="Imagen para compartir (1200x630)",
    description="JPEG generado a partir de la imagen principal y cacheado en el "
    "almacenamiento. Errores: 404 si la obra no es visible, no tiene imagen o el "
    "archivo de origen no existe.",
    responses={200: {"content": {"image/jpeg": {}}}},
)
def get_artwork_og_image(artwork_id: int, session: SessionDep, storage: StorageDep) -> Response:
    artwork_service.get_public(session, artwork_id)
    image = artwork_service.primary_image(session, artwork_id)
    if image is None or image.id is None:
        raise not_found("La obra no tiene imagen.")
    content = og_image_service.get_or_create_og_image(
        storage, artwork_id, image.id, image.storage_key
    )
    if content is None:
        raise not_found("La imagen de la obra no esta disponible.")
    return Response(
        content=content,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get(
    "/artworks/{artwork_id}",
    response_model=ArtworkDetail,
    summary="Detalle de una obra",
    description="Errores: 404 si no existe, es un borrador o su artista esta desactivado.",
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


@router.post(
    "/track",
    status_code=204,
    summary="Registrar una visita (sin cookies ni datos personales)",
    description="Suma 1 al contador diario agregado de la obra (o general si `artwork_id` es "
    "null). No se guarda IP ni user-agent. Si la obra no existe o no es publica se ignora "
    "en silencio. Errores: 429 si se supera el limite por IP.",
    dependencies=[Depends(rate_limit("track", _track_limits))],
)
def track_visit(body: TrackRequest, session: SessionDep) -> Response:
    visit_service.record_visit(session, body.artwork_id)
    return Response(status_code=204)


@router.get(
    "/push/public-key",
    response_model=PushPublicKey,
    summary="Clave publica VAPID para suscribirse a Web Push",
    description="`public_key` es null si el push no esta configurado en el servidor.",
)
def push_public_key() -> PushPublicKey:
    settings = get_settings()
    return PushPublicKey(public_key=settings.vapid_public_key if settings.push_enabled else None)
