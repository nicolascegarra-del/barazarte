"""Suscripciones Web Push (VAPID) y envio de avisos al artista."""

import json
import logging

from pywebpush import WebPushException, webpush
from sqlmodel import Session, col, select

from app.core.config import get_settings
from app.models import Inquiry, PushSubscription
from app.schemas.push import PushSubscribe
from app.services.inquiry_service import count_unread

logger = logging.getLogger(__name__)

PUSH_TTL_SECONDS = 24 * 3600
_GONE_STATUS_CODES = (404, 410)


def subscribe(session: Session, artist_id: int, data: PushSubscribe) -> None:
    """Alta idempotente por endpoint; si pertenecia a otro artista se reasigna."""
    subscription = session.exec(
        select(PushSubscription).where(PushSubscription.endpoint == data.endpoint)
    ).first()
    if subscription is None:
        subscription = PushSubscription(
            artist_id=artist_id,
            endpoint=data.endpoint,
            p256dh=data.keys.p256dh,
            auth=data.keys.auth,
        )
    else:
        subscription.artist_id = artist_id
        subscription.p256dh = data.keys.p256dh
        subscription.auth = data.keys.auth
    session.add(subscription)
    session.commit()


def unsubscribe(session: Session, artist_id: int, endpoint: str) -> None:
    """Borra la suscripcion si es del artista; si no existe no hace nada."""
    subscription = session.exec(
        select(PushSubscription).where(
            PushSubscription.endpoint == endpoint, PushSubscription.artist_id == artist_id
        )
    ).first()
    if subscription is not None:
        session.delete(subscription)
        session.commit()


def _build_payload(session: Session, inquiry: Inquiry) -> str:
    return json.dumps(
        {
            "title": "Nueva consulta",
            "body": f"{inquiry.name} pregunta por «{inquiry.artwork_title}»",
            "url": "/panel/consultas",
            "unread": count_unread(session, inquiry.artist_id),
        },
        ensure_ascii=False,
    )


def send_new_inquiry_push(session: Session, inquiry_id: int) -> None:
    """Envia el aviso a todas las suscripciones del artista de la consulta.

    Con 404/410 el navegador ya no existe: se borra la suscripcion. Otros fallos se
    registran sin datos personales ni claves y no frenan al resto de envios.
    """
    settings = get_settings()
    if not settings.push_enabled:
        return
    inquiry = session.get(Inquiry, inquiry_id)
    if inquiry is None:
        logger.warning("Consulta %s no existe; push omitido", inquiry_id)
        return
    subscriptions = list(
        session.exec(
            select(PushSubscription).where(col(PushSubscription.artist_id) == inquiry.artist_id)
        )
    )
    if not subscriptions:
        return
    payload = _build_payload(session, inquiry)
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                },
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_subject},
                ttl=PUSH_TTL_SECONDS,
            )
        except WebPushException as exc:
            status_code = getattr(exc.response, "status_code", None)
            if status_code in _GONE_STATUS_CODES:
                session.delete(subscription)
                session.commit()
            else:
                logger.warning(
                    "Fallo al enviar push (suscripcion %s, estado %s)", subscription.id, status_code
                )
        except Exception:
            logger.exception("Error inesperado enviando push (suscripcion %s)", subscription.id)
