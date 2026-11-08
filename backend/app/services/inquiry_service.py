"""Consultas de compradores: alta publica y gestion desde el panel."""

import logging
from typing import Any

from sqlalchemy import func
from sqlmodel import Session, col, select

from app.core.errors import not_found
from app.models import Inquiry, InquiryStatus
from app.schemas.common import PaginationParams
from app.schemas.inquiry import InquiryCreate
from app.services.artwork_service import get_public

logger = logging.getLogger(__name__)


def enqueue_inquiry_emails(inquiry_id: int) -> None:
    """Encola los dos emails. Si el broker falla la consulta ya esta guardada: se registra
    el error (el artista la vera en el panel) y no se devuelve fallo al comprador."""
    from app.tasks.email import send_artist_notification, send_buyer_confirmation

    try:
        send_artist_notification.delay(inquiry_id)
        send_buyer_confirmation.delay(inquiry_id)
    except Exception:
        logger.exception("No se pudo encolar el email de la consulta %s", inquiry_id)


def create_inquiry(session: Session, artwork_id: int, data: InquiryCreate) -> Inquiry:
    artwork = get_public(session, artwork_id)
    inquiry = Inquiry(
        artist_id=artwork.artist_id,
        artwork_id=artwork.id,
        artwork_title=artwork.title,
        name=data.name,
        email=str(data.email).lower(),
        phone=data.phone,
        message=data.message,
    )
    session.add(inquiry)
    session.commit()
    session.refresh(inquiry)
    assert inquiry.id is not None  # noqa: S101
    enqueue_inquiry_emails(inquiry.id)
    return inquiry


def list_inquiries(
    session: Session,
    artist_id: int,
    params: PaginationParams,
    status: InquiryStatus | None,
    artwork_id: int | None,
) -> tuple[list[Inquiry], int]:
    conditions: list[Any] = [Inquiry.artist_id == artist_id]
    if status is not None:
        conditions.append(Inquiry.status == status)
    if artwork_id is not None:
        conditions.append(Inquiry.artwork_id == artwork_id)
    total = session.exec(select(func.count()).select_from(Inquiry).where(*conditions)).one()
    statement = (
        select(Inquiry)
        .where(*conditions)
        .order_by(col(Inquiry.created_at).desc(), col(Inquiry.id).desc())
        .offset(params.offset)
        .limit(params.page_size)
    )
    return list(session.exec(statement)), total


def update_status(
    session: Session, artist_id: int, inquiry_id: int, status: InquiryStatus
) -> Inquiry:
    inquiry = session.get(Inquiry, inquiry_id)
    if inquiry is None or inquiry.artist_id != artist_id:
        raise not_found("Consulta no encontrada.")
    inquiry.status = status
    session.add(inquiry)
    session.commit()
    session.refresh(inquiry)
    return inquiry
