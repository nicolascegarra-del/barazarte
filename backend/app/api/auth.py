"""Autenticacion del artista: access token en el cuerpo, refresh token en cookie HttpOnly."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response
from sqlmodel import Session

from app.api.deps import CurrentArtist, SessionDep
from app.core.config import get_settings
from app.core.errors import unauthorized
from app.core.rate_limit import rate_limit
from app.core.security import TokenType, create_token, decode_token
from app.models import Artist
from app.schemas.auth import (
    Accepted,
    ArtistPrivate,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.services import account_service, artwork_service, auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth"


def _login_limits() -> tuple[int, int]:
    settings = get_settings()
    return settings.login_rate_limit, settings.login_rate_window_seconds


def _register_limits() -> tuple[int, int]:
    settings = get_settings()
    return settings.register_rate_limit, settings.register_rate_window_seconds


def _reset_limits() -> tuple[int, int]:
    settings = get_settings()
    return settings.password_reset_rate_limit, settings.password_reset_rate_window_seconds


def _artist_private(session: Session, artist: Artist) -> ArtistPrivate:
    assert artist.id is not None  # noqa: S101
    return ArtistPrivate(
        id=artist.id,
        email=artist.email,
        display_name=artist.display_name,
        bio=artist.bio,
        website=artist.website,
        is_admin=artist.is_admin,
        max_artworks=artist.max_artworks,
        artworks_count=artwork_service.count_for_artist(session, artist.id),
    )


def _issue_tokens(session: Session, artist: Artist, response: Response) -> TokenResponse:
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
        artist=_artist_private(session, artist),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesion",
    description="Devuelve el access token (15 min) y fija el refresh token (7 dias) en cookie "
    "HttpOnly SameSite=Strict. Errores: 401 credenciales invalidas, 403 ACCOUNT_DISABLED o "
    "EMAIL_NOT_VERIFIED (solo tras validar la contrasena), 429 demasiados intentos.",
    dependencies=[Depends(rate_limit("login", _login_limits))],
)
def login(body: LoginRequest, response: Response, session: SessionDep) -> TokenResponse:
    artist = auth_service.authenticate(session, str(body.email), body.password)
    return _issue_tokens(session, artist, response)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar el access token",
    description="Usa la cookie de refresh; rota la cookie. Errores: 401 si falta, caduco o "
    "la cuenta esta desactivada.",
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
    return _issue_tokens(session, artist, response)


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
def me(artist: CurrentArtist, session: SessionDep) -> ArtistPrivate:
    return _artist_private(session, artist)


@router.post(
    "/register",
    response_model=Accepted,
    status_code=202,
    summary="Registro publico de artistas",
    description="Crea la cuenta sin verificar y envia un email con el enlace de confirmacion. "
    "Responde siempre 202 (no revela si el email ya existe; en ese caso se avisa por email). "
    "La cuenta se activa automaticamente al verificar el email. "
    "Errores: 422 validacion (clave minima 10 caracteres), 429 demasiados intentos.",
    dependencies=[Depends(rate_limit("register", _register_limits))],
)
def register(body: RegisterRequest, session: SessionDep) -> Accepted:
    account_service.register_artist(session, body)
    return Accepted()


@router.post(
    "/verify-email",
    status_code=204,
    summary="Verificar el email",
    description="Token de un solo uso con caducidad de 48 h. "
    "Errores: 400 INVALID_TOKEN si es invalido, caducado o ya usado.",
    dependencies=[Depends(rate_limit("verify-email", _login_limits))],
)
def verify_email(body: VerifyEmailRequest, session: SessionDep) -> Response:
    account_service.verify_email(session, body.token)
    return Response(status_code=204)


@router.post(
    "/password-reset/request",
    response_model=Accepted,
    status_code=202,
    summary="Solicitar restablecimiento de contrasena",
    description="Responde siempre 202. Si la cuenta existe y esta activa se envia un email con "
    "un enlace de un solo uso que caduca en 1 hora. Errores: 429 demasiados intentos.",
    dependencies=[Depends(rate_limit("password-reset", _reset_limits))],
)
def request_password_reset(body: PasswordResetRequest, session: SessionDep) -> Accepted:
    account_service.request_password_reset(session, str(body.email))
    return Accepted()


@router.post(
    "/password-reset/confirm",
    status_code=204,
    summary="Fijar una nueva contrasena con el token del email",
    description="El token se invalida al cambiar la contrasena. "
    "Errores: 400 INVALID_TOKEN, 422 clave demasiado corta (min. 10).",
    dependencies=[Depends(rate_limit("password-reset-confirm", _login_limits))],
)
def confirm_password_reset(body: PasswordResetConfirm, session: SessionDep) -> Response:
    account_service.confirm_password_reset(session, body.token, body.new_password)
    return Response(status_code=204)
