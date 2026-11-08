import re
from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

# Hostname o IP (v4/v6) sin esquema, puerto ni espacios
_HOST_PATTERN = re.compile(r"[A-Za-z0-9]([A-Za-z0-9.:\-]*[A-Za-z0-9])?|\[[0-9A-Fa-f:.]+\]")


class ArtistStats(BaseModel):
    total: int
    active: int
    disabled: int
    unverified: int


class ArtworkStats(BaseModel):
    total: int
    borrador: int
    publicado: int
    reservado: int
    vendido: int


class InquiryStats(BaseModel):
    total: int
    nueva: int
    contactado: int
    vendida: int


class VisitDay(BaseModel):
    date: str = Field(description="YYYY-MM-DD (UTC)")
    count: int


class VisitStats(BaseModel):
    total: int
    last_30_days: int
    by_day: list[VisitDay]


class AdminStats(BaseModel):
    artists: ArtistStats
    artworks: ArtworkStats
    inquiries: InquiryStats
    visits: VisitStats


class AdminArtistRead(BaseModel):
    id: int
    email: str
    display_name: str
    is_active: bool
    email_verified: bool
    is_admin: bool
    max_artworks: int | None
    artworks_count: int
    published_count: int = Field(description="Obras en estado publicado")
    inquiries_count: int = Field(description="Consultas (contactos) recibidas")
    visits_count: int = Field(description="Visitas a sus obras")
    created_at: datetime


class AdminArtistUpdate(BaseModel):
    """Campos ausentes = sin cambio. `max_artworks: null` = ilimitado."""

    is_active: bool | None = None
    max_artworks: int | None = Field(default=None, ge=0)


class TrackRequest(BaseModel):
    artwork_id: int | None = Field(default=None, ge=1)


class SmtpSecurity(StrEnum):
    NONE = "none"
    STARTTLS = "starttls"
    SSL = "ssl"


class EmailSettingsRead(BaseModel):
    host: str
    port: int
    username: str | None
    has_password: bool
    security: SmtpSecurity
    from_name: str
    from_email: str
    source: Literal["database", "environment"]


class EmailSettingsUpdate(BaseModel):
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(
        default=None,
        max_length=500,
        description="Ausente/null = conservar la actual; cadena vacia = borrarla.",
    )
    security: SmtpSecurity
    from_name: str = Field(min_length=1, max_length=100)
    from_email: EmailStr

    @field_validator("host")
    @classmethod
    def _valid_host(cls, value: str) -> str:
        value = value.strip()
        if not _HOST_PATTERN.fullmatch(value):
            raise ValueError("El servidor debe ser un nombre de host o IP sin esquema ni espacios.")
        return value

    @field_validator("from_name")
    @classmethod
    def _single_line_name(cls, value: str) -> str:
        value = value.strip()
        if not value or any(char in value for char in "\r\n<>"):
            raise ValueError("El nombre del remitente no es valido.")
        return value

    @field_validator("username")
    @classmethod
    def _clean_username(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if any(char in value for char in "\r\n"):
            raise ValueError("El usuario no es valido.")
        return value or None


class EmailTestRequest(BaseModel):
    to: EmailStr | None = None


class EmailTestResult(BaseModel):
    status: Literal["sent"] = "sent"
