from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.database import get_session
from app.core.errors import forbidden, unauthorized
from app.core.security import TokenType, decode_token
from app.models import Artist
from app.services.auth_service import get_active_artist

SessionDep = Annotated[Session, Depends(get_session)]
_bearer = HTTPBearer(auto_error=False)


def get_current_artist(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Artist:
    if credentials is None:
        raise unauthorized("Falta el token de acceso.")
    artist_id = decode_token(credentials.credentials, TokenType.ACCESS)
    return get_active_artist(session, artist_id)


CurrentArtist = Annotated[Artist, Depends(get_current_artist)]


def get_current_admin(artist: CurrentArtist) -> Artist:
    if not artist.is_admin:
        raise forbidden("Se requieren permisos de administrador.")
    return artist


CurrentAdmin = Annotated[Artist, Depends(get_current_admin)]
