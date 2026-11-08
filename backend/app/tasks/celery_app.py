from celery import Celery

from app.core.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "barazarte",
    broker=_settings.redis_url,
    backend=_settings.redis_url,
    include=["app.tasks.email"],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    result_expires=3600,
)
