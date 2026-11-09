from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Text
from sqlmodel import Field, SQLModel

from app.models.base import enum_column, timestamp_column, utcnow
from app.models.enums import InquiryStatus


class Inquiry(SQLModel, table=True):
    """Consulta de un comprador. `artist_id` y `artwork_title` se denormalizan para que
    el historial de consultas sobreviva al borrado de la obra."""

    __tablename__ = "inquiries"
    __table_args__ = (
        Index("ix_inquiries_artist_status", "artist_id", "status"),
        # Contar las no leidas de un artista (read_at IS NULL) sin recorrer todas sus consultas
        Index("ix_inquiries_artist_read", "artist_id", "read_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    artist_id: int = Field(
        sa_column=Column(Integer, ForeignKey("artists.id", ondelete="CASCADE"), nullable=False)
    )
    artwork_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer, ForeignKey("artworks.id", ondelete="SET NULL"), nullable=True, index=True
        ),
    )
    artwork_title: str = Field(max_length=200)
    name: str = Field(max_length=120)
    email: str = Field(max_length=254)
    phone: str | None = Field(default=None, max_length=30)
    message: str = Field(sa_column=Column(Text, nullable=False))
    status: InquiryStatus = Field(default=InquiryStatus.NEW, sa_column=enum_column(InquiryStatus))
    created_at: datetime = Field(default_factory=utcnow, sa_column=timestamp_column())
    # None = sin leer por el artista (UTC)
    read_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
