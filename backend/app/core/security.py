"""Hash de contrasenas (bcrypt) y tokens JWT."""

import hashlib
import hmac
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from functools import lru_cache
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings
from app.core.errors import unauthorized

JWT_ALGORITHM = "HS256"


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(password: str) -> str:
    rounds = get_settings().bcrypt_rounds
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=rounds)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        # Hash corrupto o contrasena que excede el limite de 72 bytes de bcrypt
        return False


@lru_cache
def _dummy_hash() -> str:
    return hash_password("dummy-password-for-timing")


def burn_password_check(password: str) -> None:
    """Gasta el mismo tiempo que una verificacion real (evita enumerar emails por timing)."""
    verify_password(password, _dummy_hash())


def create_token(subject: int, token_type: TokenType) -> str:
    settings = get_settings()
    lifetime = (
        timedelta(minutes=settings.jwt_access_expire_minutes)
        if token_type is TokenType.ACCESS
        else timedelta(days=settings.jwt_refresh_expire_days)
    )
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type.value,
        "iat": now,
        "exp": now + lifetime,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)


def decode_token(token: str, expected_type: TokenType) -> int:
    """Devuelve el id del sujeto o lanza 401 si el token no es valido."""
    try:
        payload = jwt.decode(
            token,
            get_settings().jwt_secret_key,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
        if payload["type"] != expected_type.value:
            raise unauthorized("Token no valido.")
        return int(payload["sub"])
    except (jwt.PyJWTError, ValueError) as exc:
        raise unauthorized("Token no valido o caducado.") from exc


class PurposeToken(StrEnum):
    """Tokens de un solo proposito (enlaces de email). Su claim `type` es distinto al de
    los access/refresh, por lo que `decode_token` los rechaza y no sirven para autenticar."""

    EMAIL_VERIFY = "email_verify"
    PASSWORD_RESET = "password_reset"  # noqa: S105


def password_fingerprint(password_hash: str) -> str:
    """Huella (HMAC) del hash actual: ligada al token de reset lo invalida al cambiar la clave."""
    key = get_settings().jwt_secret_key.encode()
    return hmac.new(key, password_hash.encode(), hashlib.sha256).hexdigest()[:24]


def create_purpose_token(
    subject: int, purpose: PurposeToken, lifetime: timedelta, fingerprint: str | None = None
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": purpose.value,
        "iat": now,
        "exp": now + lifetime,
        "jti": uuid.uuid4().hex,
    }
    if fingerprint is not None:
        payload["fp"] = fingerprint
    return jwt.encode(payload, get_settings().jwt_secret_key, algorithm=JWT_ALGORITHM)


def decode_purpose_token(token: str, purpose: PurposeToken) -> tuple[int, str | None]:
    """Devuelve (id_sujeto, huella) o lanza ValueError si es invalido, caducado o de otro tipo."""
    try:
        payload = jwt.decode(
            token,
            get_settings().jwt_secret_key,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
        if payload["type"] != purpose.value:
            raise ValueError("tipo de token incorrecto")
        return int(payload["sub"]), payload.get("fp")
    except jwt.PyJWTError as exc:
        raise ValueError("token no valido o caducado") from exc
