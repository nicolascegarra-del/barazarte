from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlmodel import Field, SQLModel

from app.models.base import timestamp_column, utcnow


class PushSubscription(SQLModel, table=True):
    """Suscripcion Web Push de un navegador del artista (un artista puede tener varias)."""

    __tablename__ = "push_subscriptions"

    id: int | None = Field(default=None, primary_key=True)
    artist_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("artists.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    endpoint: str = Field(sa_column=Column(Text, nullable=False, unique=True))
    p256dh: str = Field(max_length=256)
    auth: str = Field(max_length=256)
    created_at: datetime = Field(default_factory=utcnow, sa_column=timestamp_column())
