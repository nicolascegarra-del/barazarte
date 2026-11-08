"""Alta de artistas, verificacion de email y reset de contrasena."""

import logging

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import hash_password, password_fingerprint
from app.models import Artist
from app.models.base import utcnow
from app.schemas.auth import RegisterRequest
from app.services import token_service

logger = logging.getLogger(__name__)

INVALID_TOKEN_MESSAGE = "El enlace no es valido o ha caducado."  # noqa: S105


def _invalid_token() -> AppError:
    return AppError(400, "INVALID_TOKEN", INVALID_TOKEN_MESSAGE, field="token")


def enqueue_account_email(kind: str, artist_id: int) -> None:
    """Encola un email de cuenta (`verification`, `password_reset`, `account_exists`).
    Si el broker falla se registra y no se rompe la peticion (respuesta uniforme)."""
    from app.tasks import email as tasks

    task = {
        "verification": tasks.send_verification_email,
        "password_reset": tasks.send_password_reset_email,
        "account_exists": tasks.send_account_exists_email,
    }[kind]
    try:
        task.delay(artist_id)
    except Exception:
        logger.exception("No se pudo encolar el email %s del artista %s", kind, artist_id)


def register_artist(session: Session, data: RegisterRequest) -> None:
    """Crea el artista (sin verificar). Si el email ya existe no se revela: se avisa por email.
    Se hashea la clave en ambas ramas para igualar tiempos de respuesta."""
    email = str(data.email).lower()
    password_hash = hash_password(data.password)
    existing = session.exec(select(Artist).where(Artist.email == email)).first()
    if existing is not None and existing.id is not None:
        enqueue_account_email("account_exists", existing.id)
        return
    artist = Artist(
        email=email,
        display_name=data.display_name,
        password_hash=password_hash,
        is_active=True,
        email_verified=False,
        max_artworks=get_settings().default_max_artworks,
    )
    session.add(artist)
    try:
        session.commit()
    except IntegrityError:
        # Registro concurrente con el mismo email: la otra peticion ya lo creo
        session.rollback()
        return
    session.refresh(artist)
    assert artist.id is not None  # noqa: S101
    enqueue_account_email("verification", artist.id)


def verify_email(session: Session, token: str) -> None:
    """Activa la cuenta. Un solo uso: si ya estaba verificada el enlace deja de valer."""
    try:
        artist_id = token_service.read_verification_token(token)
    except ValueError as exc:
        raise _invalid_token() from exc
    artist = session.get(Artist, artist_id)
    if artist is None or artist.email_verified:
        raise _invalid_token()
    artist.email_verified = True
    artist.updated_at = utcnow()
    session.add(artist)
    session.commit()


def request_password_reset(session: Session, email: str) -> None:
    artist = session.exec(select(Artist).where(Artist.email == email.lower())).first()
    if artist is not None and artist.is_active and artist.id is not None:
        enqueue_account_email("password_reset", artist.id)


def confirm_password_reset(session: Session, token: str, new_password: str) -> None:
    try:
        artist_id, fingerprint = token_service.read_password_reset_token(token)
    except ValueError as exc:
        raise _invalid_token() from exc
    artist = session.get(Artist, artist_id)
    if artist is None or not artist.is_active:
        raise _invalid_token()
    # Si la clave ya cambio, la huella no coincide: el enlace es de un solo uso
    if fingerprint != password_fingerprint(artist.password_hash):
        raise _invalid_token()
    artist.password_hash = hash_password(new_password)
    artist.updated_at = utcnow()
    session.add(artist)
    session.commit()
