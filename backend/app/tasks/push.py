"""Tarea Celery de notificaciones Web Push."""

from sqlmodel import Session

from app.core.database import get_engine
from app.services.push_service import send_new_inquiry_push
from app.tasks.celery_app import celery_app


@celery_app.task(name="push.send_new_inquiry")
def send_new_inquiry(inquiry_id: int) -> None:
    # Sin reintentos automaticos: un reintento duplicaria avisos ya entregados
    with Session(get_engine()) as session:
        send_new_inquiry_push(session, inquiry_id)
