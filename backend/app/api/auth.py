"""Autenticacion del artista: access token en el cuerpo, refresh token en cookie HttpOnly."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response

from app.api.deps import CurrentArtist, SessionDep
from app.core.config import get_settings
from app.core.errors import unauthorized
from app.core.rate_limit import rate_limit
from app.core.security import TokenType, create_token, decode_token
from app.models import Artist
from app.schemas.auth import ArtistPrivate, LoginRequest, TokenResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"


def _login_limits() -> tuple[int, int]:
    settings = get_settings()
    return settings.login_rate_limit, settings.login_rate_window_seconds


def _artist_private(artist: Artist) -> ArtistPrivate:
    assert artist.id is not None  # noqa: S101
    return ArtistPrivate(
        id=artist.id,
        email=artist.email,
        display_name=artist.display_name,
        bio=artist.bio,
        website=artist.website,
    )


def _issue_tokens(artist: Artist, response: Response) -> TokenResponse:
    settings = get_settings()
    assert artist.id is not None  # noqa: S101
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=create_token(artist.id, TokenType.REFRESH),
        max_age=settings.jwt_refresh_expire_days * 24 * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
    )
    return TokenResponse(
        access_token=create_token(artist.id, TokenType.ACCESS),
        expires_in=settings.jwt_access_expire_minutes * 60,
        artist=_artist_private(artist),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesion",
    description="Devuelve el access token (15 min) y fija el refresh token (7 dias) en cookie "
    "HttpOnly SameSite=Strict. Errores: 401 credenciales invalidas, 429 demasiados intentos.",
    dependencies=[Depends(rate_limit("login", _login_limits))],
)
def login(body: LoginRequest, response: Response, session: SessionDep) -> TokenResponse:
    artist = auth_service.authenticate(session, str(body.email), body.password)
    return _issue_tokens(artist, response)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar el access token",
    description="Usa la cookie de refresh; rota la cookie. Errores: 401 si falta o caduco.",
    dependencies=[Depends(rate_limit("refresh", _login_limits))],
)
def refresh(
    response: Response,
    session: SessionDep,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
) -> TokenResponse:
    if not refresh_token:
        raise unauthorized("Sesion no iniciada.")
    artist_id = decode_token(refresh_token, TokenType.REFRESH)
    artist = auth_service.get_active_artist(session, artist_id)
    return _issue_tokens(artist, response)


@router.post("/logout", status_code=204, summary="Cerrar sesion")
def logout(response: Response) -> Response:
    settings = get_settings()
    response.delete_cookie(
        REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
    )
    response.status_code = 204
    return response


@router.get("/me", response_model=ArtistPrivate, summary="Artista autenticado")
def me(artist: CurrentArtist) -> ArtistPrivate:
    return _artist_private(artist)
