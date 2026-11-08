"""Tokens firmados de verificacion de email y reset de contrasena."""

from datetime import timedelta

from app.core.config import get_settings
from app.core.security import (
    PurposeToken,
    create_purpose_token,
    decode_purpose_token,
    password_fingerprint,
)
from app.models import Artist


def create_verification_token(artist: Artist) -> str:
    assert artist.id is not None  # noqa: S101
    lifetime = timedelta(hours=get_settings().email_verify_expire_hours)
    return create_purpose_token(artist.id, PurposeToken.EMAIL_VERIFY, lifetime)


def create_password_reset_token(artist: Artist) -> str:
    assert artist.id is not None  # noqa: S101
    lifetime = timedelta(minutes=get_settings().password_reset_expire_minutes)
    return create_purpose_token(
        artist.id,
        PurposeToken.PASSWORD_RESET,
        lifetime,
        fingerprint=password_fingerprint(artist.password_hash),
    )


def read_verification_token(token: str) -> int:
    """Devuelve el id del artista o lanza ValueError."""
    return decode_purpose_token(token, PurposeToken.EMAIL_VERIFY)[0]


def read_password_reset_token(token: str) -> tuple[int, str]:
    """Devuelve (id del artista, huella de la clave) o lanza ValueError."""
    artist_id, fingerprint = decode_purpose_token(token, PurposeToken.PASSWORD_RESET)
    if fingerprint is None:
        raise ValueError("token sin huella")
    return artist_id, fingerprint
