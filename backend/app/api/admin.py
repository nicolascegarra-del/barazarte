"""Panel de administracion (requiere Artist.is_admin). El admin nunca ve contrasenas."""

import logging
import smtplib
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentAdmin, SessionDep, get_current_admin
from app.schemas.admin import (
    AdminArtistRead,
    AdminArtistUpdate,
    AdminStats,
    EmailSettingsRead,
    EmailSettingsUpdate,
    EmailTestRequest,
    EmailTestResult,
)
from app.schemas.auth import Accepted
from app.schemas.common import Page, PaginationParams
from app.services import account_service, admin_service, email_service, email_settings_service

TEST_TIMEOUT_SECONDS = 10

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])


@router.get(
    "/stats",
    response_model=AdminStats,
    summary="Estadisticas globales",
    description="Artistas, obras, consultas y visitas (ultimos 30 dias, rellenando ceros). "
    "Errores: 401 sin sesion, 403 si no es administrador.",
)
def get_stats(session: SessionDep) -> AdminStats:
    return admin_service.get_stats(session)


@router.get(
    "/artists",
    response_model=Page[AdminArtistRead],
    summary="Listado de artistas",
    description="Paginado; `q` busca en nombre y email. Incluye contadores de obras, "
    "consultas (contactos) y visitas. Errores: 403 si no es administrador.",
)
def list_artists(
    session: SessionDep,
    pagination: Annotated[PaginationParams, Depends()],
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> Page[AdminArtistRead]:
    items, total = admin_service.list_artists(session, pagination, q)
    return Page.build(items, total, pagination)


@router.patch(
    "/artists/{artist_id}",
    response_model=AdminArtistRead,
    summary="Activar/desactivar artista o cambiar su limite de obras",
    description="`max_artworks: null` = ilimitado; un campo ausente no cambia. Errores: "
    "403 si el objetivo es otro admin, 404 artista inexistente, "
    "409 CANNOT_DISABLE_SELF si el admin intenta desactivarse.",
)
def update_artist(
    artist_id: int, body: AdminArtistUpdate, admin: CurrentAdmin, session: SessionDep
) -> AdminArtistRead:
    return admin_service.update_artist(session, admin, artist_id, body)


@router.post(
    "/artists/{artist_id}/reset-password",
    status_code=202,
    response_model=Accepted,
    summary="Enviar al artista el email de restablecimiento de contrasena",
    description="El admin nunca ve ni fija contrasenas. Errores: 403 otro admin, "
    "404 inexistente, 409 cuenta desactivada.",
)
def reset_artist_password(artist_id: int, admin: CurrentAdmin, session: SessionDep) -> Accepted:
    artist = admin_service.get_artist_for_reset(session, admin, artist_id)
    assert artist.id is not None  # noqa: S101
    account_service.enqueue_account_email("password_reset", artist.id)
    return Accepted()


@router.get(
    "/email-settings",
    response_model=EmailSettingsRead,
    summary="Cuenta de correo (SMTP) de la plataforma",
    description="Nunca devuelve la contrasena (`has_password`). `source` indica si viene de la "
    "base de datos o de las variables de entorno. Errores: 403 si no es administrador.",
)
def get_email_settings(session: SessionDep) -> EmailSettingsRead:
    return email_settings_service.read_email_settings(session)


@router.put(
    "/email-settings",
    response_model=EmailSettingsRead,
    summary="Guardar la cuenta de correo (SMTP) de la plataforma",
    description="`password` ausente/null conserva la actual; cadena vacia la borra. Errores: "
    "403 si no es administrador, 422 datos no validos.",
)
def put_email_settings(body: EmailSettingsUpdate, session: SessionDep) -> EmailSettingsRead:
    return email_settings_service.update_email_settings(session, body)


@router.post(
    "/email-settings/test",
    response_model=EmailTestResult,
    summary="Enviar un email de prueba ahora mismo",
    description="Envio sincrono (timeout 10 s) a `to` o, por defecto, al email del admin. "
    "Errores: 403 si no es administrador, 502 EMAIL_SEND_FAILED si el servidor SMTP falla.",
)
def send_test_email(
    admin: CurrentAdmin,
    session: SessionDep,
    body: EmailTestRequest | None = None,
) -> EmailTestResult:
    recipient = str(body.to) if body and body.to else admin.email
    try:
        email_service.send_email(
            email_service.build_test_email(recipient), session=session, timeout=TEST_TIMEOUT_SECONDS
        )
    except (OSError, smtplib.SMTPException) as error:
        # Solo el tipo de error: el mensaje del servidor podria incluir datos de la cuenta
        logger.warning("Fallo el email de prueba SMTP: %s", type(error).__name__)
        raise email_settings_service.email_send_failed(error) from error
    return EmailTestResult()
