from sqlmodel import Session, select

from app.core.errors import unauthorized
from app.core.security import burn_password_check, verify_password
from app.models import Artist


def authenticate(session: Session, email: str, password: str) -> Artist:
    """Valida credenciales. El mensaje de error es identico para email desconocido,
    contrasena incorrecta o cuenta inactiva (no revela que cuentas existen)."""
    artist = session.exec(select(Artist).where(Artist.email == email.lower())).first()
    if artist is None:
        burn_password_check(password)
        raise unauthorized("Email o contrasena incorrectos.")
    if not verify_password(password, artist.password_hash) or not artist.is_active:
        raise unauthorized("Email o contrasena incorrectos.")
    return artist


def get_active_artist(session: Session, artist_id: int) -> Artist:
    artist = session.get(Artist, artist_id)
    if artist is None or not artist.is_active:
        raise unauthorized("Token no valido.")
    return artist
