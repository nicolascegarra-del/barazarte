from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, ForeignKey, Index, Integer, Numeric, Text
from sqlmodel import Field, SQLModel

from app.models.base import enum_column, timestamp_column, utcnow
from app.models.enums import ArtworkStatus


class Artwork(SQLModel, table=True):
    __tablename__ = "artworks"
    __table_args__ = (Index("ix_artworks_status_created", "status", "created_at"),)

    id: int | None = Field(default=None, primary_key=True)
    artist_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("artists.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    title: str = Field(max_length=200)
    technique: str = Field(max_length=120)
    width_cm: Decimal = Field(sa_column=Column(Numeric(7, 2), nullable=False))
    height_cm: Decimal = Field(sa_column=Column(Numeric(7, 2), nullable=False))
    depth_cm: Decimal | None = Field(default=None, sa_column=Column(Numeric(7, 2), nullable=True))
    year: int
    price: Decimal | None = Field(default=None, sa_column=Column(Numeric(10, 2), nullable=True))
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    status: ArtworkStatus = Field(default=ArtworkStatus.DRAFT, sa_column=enum_column(ArtworkStatus))
    created_at: datetime = Field(default_factory=utcnow, sa_column=timestamp_column())
    updated_at: datetime = Field(default_factory=utcnow, sa_column=timestamp_column())


class ArtworkImage(SQLModel, table=True):
    __tablename__ = "artwork_images"

    id: int | None = Field(default=None, primary_key=True)
    artwork_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("artworks.id", ondelete="CASCADE"), nullable=False, index=True
        )
    )
    storage_key: str = Field(max_length=255)
    thumb_key: str = Field(max_length=255)
    alt_text: str | None = Field(default=None, max_length=200)
    position: int = Field(default=0)
    width: int
    height: int
    created_at: datetime = Field(default_factory=utcnow, sa_column=timestamp_column())
