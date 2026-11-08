"""Cifrado simetrico (Fernet) de secretos guardados en BD, p. ej. la clave SMTP."""

import base64
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.core.config import get_settings

_HKDF_INFO = b"barazarte-settings-encryption-v1"


class SecretDecryptionError(Exception):
    """El valor cifrado no se puede descifrar (clave cambiada o dato corrupto)."""


@lru_cache
def _fernet_for(explicit_key: str, jwt_secret: str) -> Fernet:
    if explicit_key:
        return Fernet(explicit_key.encode())
    derived = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=_HKDF_INFO).derive(
        jwt_secret.encode()
    )
    return Fernet(base64.urlsafe_b64encode(derived))


def _fernet() -> Fernet:
    settings = get_settings()
    return _fernet_for(settings.settings_encryption_key, settings.jwt_secret_key)


def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_secret(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as error:
        raise SecretDecryptionError("No se puede descifrar el secreto guardado.") from error
