"""Configuracion SMTP de la plataforma: BD (editable por el admin) con las variables de entorno
como valor por defecto cuando no hay fila guardada."""

import logging
import smtplib
from dataclasses import dataclass
from email.utils import parseaddr

from sqlmodel import Session

from app.core.config import get_settings
from app.core.crypto import SecretDecryptionError, decrypt_secret, encrypt_secret
from app.core.errors import AppError
from app.models import EmailSettings
from app.models.base import utcnow
from app.models.email_settings import EMAIL_SETTINGS_ID
from app.schemas.admin import EmailSettingsRead, EmailSettingsUpdate, SmtpSecurity

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    username: str | None
    password: str | None
    security: SmtpSecurity
    from_name: str
    from_email: str
    source: str  # "database" | "environment"

    def __repr__(self) -> str:  # nunca exponer la contrasena en logs/trazas
        return f"SmtpConfig(host={self.host!r}, port={self.port}, source={self.source!r})"


def _environment_config() -> SmtpConfig:
    settings = get_settings()
    from_name, from_email = parseaddr(settings.mail_from)
    return SmtpConfig(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user or None,
        password=settings.smtp_password or None,
        security=SmtpSecurity.STARTTLS if settings.smtp_starttls else SmtpSecurity.NONE,
        from_name=from_name,
        from_email=from_email or settings.mail_from,
        source="environment",
    )


def get_smtp_config(session: Session) -> SmtpConfig:
    """Configuracion efectiva. Se lee en cada envio: el worker Celery es otro proceso."""
    row = session.get(EmailSettings, EMAIL_SETTINGS_ID)
    if row is None:
        return _environment_config()
    password: str | None = None
    if row.password_encrypted:
        try:
            password = decrypt_secret(row.password_encrypted)
        except SecretDecryptionError:
            # Clave de cifrado cambiada: el servidor SMTP rechazara el login y se vera el error
            logger.error("No se pudo descifrar la contrasena SMTP guardada; vuelve a introducirla")
    return SmtpConfig(
        host=row.host,
        port=row.port,
        username=row.username,
        password=password,
        security=SmtpSecurity(row.security),
        from_name=row.from_name,
        from_email=row.from_email,
        source="database",
    )


def read_email_settings(session: Session) -> EmailSettingsRead:
    row = session.get(EmailSettings, EMAIL_SETTINGS_ID)
    config = get_smtp_config(session)
    has_password = bool(row.password_encrypted) if row is not None else config.password is not None
    return EmailSettingsRead(
        host=config.host,
        port=config.port,
        username=config.username,
        has_password=has_password,
        security=config.security,
        from_name=config.from_name,
        from_email=config.from_email,
        source="database" if row is not None else "environment",
    )


def update_email_settings(session: Session, body: EmailSettingsUpdate) -> EmailSettingsRead:
    row = session.get(EmailSettings, EMAIL_SETTINGS_ID)
    if row is None:
        # La contrasena del entorno no se copia a BD: solo lo que envie el admin
        row = EmailSettings(
            host=body.host,
            port=body.port,
            security=body.security.value,
            from_name=body.from_name,
            from_email=str(body.from_email),
        )
    row.host = body.host
    row.port = body.port
    row.username = body.username
    row.security = body.security.value
    row.from_name = body.from_name
    row.from_email = str(body.from_email)
    if body.password is not None:
        row.password_encrypted = encrypt_secret(body.password) if body.password else None
    row.updated_at = utcnow()
    session.add(row)
    session.commit()
    return read_email_settings(session)


def send_error_message(error: Exception) -> str:
    """Mensaje legible en espanol para un fallo de envio; sin credenciales ni trazas."""
    if isinstance(error, smtplib.SMTPAuthenticationError):
        return "El servidor rechazo el usuario o la contrasena."
    if isinstance(error, smtplib.SMTPRecipientsRefused):
        return "El servidor rechazo el destinatario."
    if isinstance(error, smtplib.SMTPSenderRefused):
        return "El servidor rechazo la direccion del remitente."
    if isinstance(error, TimeoutError):
        return "El servidor de correo no respondio a tiempo."
    if isinstance(error, smtplib.SMTPConnectError | ConnectionError):
        return "No se pudo conectar con el servidor de correo (revisa servidor y puerto)."
    if isinstance(error, OSError | smtplib.SMTPServerDisconnected):
        return (
            "No se pudo establecer la conexion con el servidor de correo "
            "(revisa servidor, puerto y tipo de seguridad)."
        )
    return "El servidor de correo no pudo enviar el mensaje de prueba."


def email_send_failed(error: Exception) -> AppError:
    return AppError(502, "EMAIL_SEND_FAILED", send_error_message(error))
