"""Construccion y envio de emails transaccionales (texto plano, SMTP)."""

import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from sqlmodel import Session

from app.core.config import get_settings
from app.core.database import get_engine
from app.models import Artist, Inquiry
from app.schemas.admin import SmtpSecurity
from app.services.email_settings_service import SmtpConfig, get_smtp_config

SEND_TIMEOUT_SECONDS = 15


def _single_line(value: str) -> str:
    """Evita inyeccion de cabeceras: colapsa saltos de linea y espacios."""
    return " ".join(value.split())


def build_artist_notification(inquiry: Inquiry, artist: Artist) -> EmailMessage:
    settings = get_settings()
    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = artist.email
    message["Reply-To"] = inquiry.email
    message["Subject"] = _single_line(f'Nueva consulta sobre "{inquiry.artwork_title}"')
    contact_phone = inquiry.phone or "no indicado"
    message.set_content(
        f"Hola {artist.display_name},\n\n"
        f'{inquiry.name} ha enviado una consulta sobre "{inquiry.artwork_title}".\n\n'
        f"Email: {inquiry.email}\n"
        f"Telefono: {contact_phone}\n\n"
        f"Mensaje:\n{inquiry.message}\n\n"
        f"Puedes responder directamente a este correo o gestionarla en el panel:\n"
        f"{settings.frontend_base_url.rstrip('/')}/panel/consultas\n"
    )
    return message


def build_buyer_confirmation(inquiry: Inquiry, artist: Artist) -> EmailMessage:
    settings = get_settings()
    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = inquiry.email
    message["Subject"] = _single_line(f'Hemos recibido tu consulta sobre "{inquiry.artwork_title}"')
    message.set_content(
        f"Hola {inquiry.name},\n\n"
        f'Gracias por tu interes en "{inquiry.artwork_title}". '
        f"{artist.display_name} ha recibido tu mensaje y se pondra en contacto contigo "
        f"lo antes posible.\n\n"
        f"Tu mensaje:\n{inquiry.message}\n\n"
        f"BarazArte\n"
    )
    return message


def _frontend_url(path: str, token: str) -> str:
    return f"{get_settings().frontend_base_url.rstrip('/')}{path}?token={token}"


def _base_message(to: str, subject: str) -> EmailMessage:
    message = EmailMessage()
    message["From"] = get_settings().mail_from
    message["To"] = to
    message["Subject"] = _single_line(subject)
    return message


def build_verification_email(artist: Artist, token: str) -> EmailMessage:
    hours = get_settings().email_verify_expire_hours
    message = _base_message(artist.email, "Confirma tu email en BarazArte")
    message.set_content(
        f"Hola {artist.display_name},\n\n"
        f"Gracias por registrarte en BarazArte. Confirma tu email para activar tu cuenta:\n"
        f"{_frontend_url('/verificar-email', token)}\n\n"
        f"El enlace caduca en {hours} horas. Si no has sido tu, ignora este mensaje.\n"
    )
    return message


def build_password_reset_email(artist: Artist, token: str) -> EmailMessage:
    minutes = get_settings().password_reset_expire_minutes
    message = _base_message(artist.email, "Restablece tu contrasena de BarazArte")
    message.set_content(
        f"Hola {artist.display_name},\n\n"
        f"Puedes elegir una nueva contrasena en este enlace:\n"
        f"{_frontend_url('/restablecer', token)}\n\n"
        f"Caduca en {minutes} minutos y solo se puede usar una vez. "
        f"Si no lo has pedido tu, ignora este mensaje.\n"
    )
    return message


def build_account_exists_email(artist: Artist) -> EmailMessage:
    base = get_settings().frontend_base_url.rstrip("/")
    message = _base_message(artist.email, "Ya tienes una cuenta en BarazArte")
    message.set_content(
        f"Hola {artist.display_name},\n\n"
        f"Alguien ha intentado registrarse en BarazArte con este email, pero ya tienes cuenta.\n"
        f"Puedes iniciar sesion en {base}/panel/login o, si olvidaste la contrasena, "
        f"restablecerla desde esa pagina.\n"
        f"Si no has sido tu, ignora este mensaje.\n"
    )
    return message


def send_email(
    message: EmailMessage,
    *,
    session: Session | None = None,
    timeout: float = SEND_TIMEOUT_SECONDS,
) -> None:
    """Envia con la cuenta SMTP de la plataforma (BD; si no hay fila, variables de entorno).

    La configuracion se lee en cada envio porque el worker Celery es otro proceso."""
    if session is not None:
        config = get_smtp_config(session)
    else:
        with Session(get_engine()) as own_session:
            config = get_smtp_config(own_session)
    deliver(message, config, timeout=timeout)


def deliver(message: EmailMessage, config: SmtpConfig, *, timeout: float) -> None:
    del message["From"]
    message["From"] = formataddr((_single_line(config.from_name), config.from_email))
    if config.security is SmtpSecurity.SSL:
        smtp: smtplib.SMTP = smtplib.SMTP_SSL(
            config.host, config.port, timeout=timeout, context=ssl.create_default_context()
        )
    else:
        smtp = smtplib.SMTP(config.host, config.port, timeout=timeout)
    with smtp:
        if config.security is SmtpSecurity.STARTTLS:
            smtp.starttls(context=ssl.create_default_context())
        if config.username:
            smtp.login(config.username, config.password or "")
        smtp.send_message(message)


def build_test_email(to: str) -> EmailMessage:
    message = _base_message(to, "Prueba de configuracion de correo de BarazArte")
    message.set_content(
        "Este es un email de prueba.\n\n"
        "Si lo has recibido, la cuenta de correo de la plataforma esta bien configurada.\n"
    )
    return message
