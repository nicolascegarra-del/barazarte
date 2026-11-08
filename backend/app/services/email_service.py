"""Construccion y envio de emails transaccionales (texto plano, SMTP)."""

import smtplib
from email.message import EmailMessage

from app.core.config import get_settings
from app.models import Artist, Inquiry


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


def send_email(message: EmailMessage) -> None:
    settings = get_settings()
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)
