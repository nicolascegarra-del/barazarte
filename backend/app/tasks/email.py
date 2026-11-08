"""Tareas Celery de email. Una tarea por destinatario para que un reintento no duplique envios."""

import logging
import smtplib
from collections.abc import Callable
from email.message import EmailMessage

from sqlmodel import Session

from app.core.database import get_engine
from app.models import Artist, Inquiry
from app.services.email_service import (
    build_account_exists_email,
    build_artist_notification,
    build_buyer_confirmation,
    build_password_reset_email,
    build_verification_email,
    send_email,
)
from app.services.token_service import (
    create_password_reset_token,
    create_verification_token,
)
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

_RETRYABLE = (OSError, smtplib.SMTPException)


def _deliver(inquiry_id: int, builder: Callable[[Inquiry, Artist], EmailMessage]) -> None:
    with Session(get_engine()) as session:
        inquiry = session.get(Inquiry, inquiry_id)
        if inquiry is None:
            logger.warning("Consulta %s no existe; email omitido", inquiry_id)
            return
        artist = session.get(Artist, inquiry.artist_id)
        if artist is None:
            logger.warning("Artista de la consulta %s no existe; email omitido", inquiry_id)
            return
        message = builder(inquiry, artist)
    send_email(message)


@celery_app.task(
    name="inquiries.send_artist_notification",
    autoretry_for=_RETRYABLE,
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def send_artist_notification(inquiry_id: int) -> None:
    _deliver(inquiry_id, build_artist_notification)


@celery_app.task(
    name="inquiries.send_buyer_confirmation",
    autoretry_for=_RETRYABLE,
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def send_buyer_confirmation(inquiry_id: int) -> None:
    _deliver(inquiry_id, build_buyer_confirmation)


def _deliver_account_email(artist_id: int, builder: Callable[[Artist], EmailMessage]) -> None:
    with Session(get_engine()) as session:
        artist = session.get(Artist, artist_id)
        if artist is None:
            logger.warning("Artista %s no existe; email omitido", artist_id)
            return
        message = builder(artist)
    send_email(message)


@celery_app.task(
    name="accounts.send_verification_email",
    autoretry_for=_RETRYABLE,
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def send_verification_email(artist_id: int) -> None:
    _deliver_account_email(
        artist_id,
        lambda artist: build_verification_email(artist, create_verification_token(artist)),
    )


@celery_app.task(
    name="accounts.send_password_reset_email",
    autoretry_for=_RETRYABLE,
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def send_password_reset_email(artist_id: int) -> None:
    # El token se genera al enviar, con el hash vigente: asi se invalida al cambiar la clave
    _deliver_account_email(
        artist_id,
        lambda artist: build_password_reset_email(artist, create_password_reset_token(artist)),
    )


@celery_app.task(
    name="accounts.send_account_exists_email",
    autoretry_for=_RETRYABLE,
    retry_backoff=True,
    retry_kwargs={"max_retries": 5},
)
def send_account_exists_email(artist_id: int) -> None:
    _deliver_account_email(artist_id, build_account_exists_email)
