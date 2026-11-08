from sqlmodel import Session, select

from app.core.errors import AppError, unauthorized
from app.core.security import burn_password_check, verify_password
from app.models import Artist


def authenticate(session: Session, email: str, password: str) -> Artist:
    """Valida credenciales. El mensaje de error es identico para email desconocido o
    contrasena incorrecta. Los bloqueos de cuenta (403) solo se revelan tras validar la
    contrasena, para no filtrar que cuentas existen."""
    artist = session.exec(select(Artist).where(Artist.email == email.lower())).first()
    if artist is None:
        burn_password_check(password)
        raise unauthorized("Email o contrasena incorrectos.")
    if not verify_password(password, artist.password_hash):
        raise unauthorized("Email o contrasena incorrectos.")
    if not artist.is_active:
        raise AppError(
            403, "ACCOUNT_DISABLED", "Tu cuenta esta desactivada. Contacta con la galeria."
        )
    if not artist.email_verified:
        raise AppError(
            403, "EMAIL_NOT_VERIFIED", "Debes confirmar tu email antes de iniciar sesion."
        )
    return artist


def get_active_artist(session: Session, artist_id: int) -> Artist:
    artist = session.get(Artist, artist_id)
    if artist is None or not artist.is_active:
        raise unauthorized("Token no valido.")
    return artist
