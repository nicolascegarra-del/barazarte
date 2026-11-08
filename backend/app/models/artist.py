from datetime import datetime

from sqlalchemy import Column, Integer, Text
from sqlmodel import Field, SQLModel

from app.core.config import get_settings
from app.models.base import timestamp_column, utcnow


class Artist(SQLModel, table=True):
    __tablename__ = "artists"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(max_length=254, unique=True, index=True)
    password_hash: str = Field(max_length=255)
    display_name: str = Field(max_length=120)
    bio: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    website: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)
    email_verified: bool = Field(default=False)
    # None = sin limite de obras. Columna explicita (sin default de SQLAlchemy): con un default
    # de columna, un None asignado a mano se sustituiria por el valor por defecto al insertar.
    max_artworks: int | None = Field(
        default_factory=lambda: get_settings().default_max_artworks,
        sa_column=Column(Integer, nullable=True),
    )
    created_at: datetime = Field(default_factory=utcnow, sa_column=timestamp_column())
    updated_at: datetime = Field(default_factory=utcnow, sa_column=timestamp_column())
