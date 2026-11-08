from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.models.enums import ArtworkStatus
from app.schemas.artist import ArtistSummary

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Technique = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Dimension = Annotated[Decimal, Field(gt=0, max_digits=7, decimal_places=2)]
PublicStatus = Literal["publicado", "reservado", "vendido"]


class ArtworkImageRead(BaseModel):
    id: int
    url: str
    thumb_url: str
    alt_text: str | None
    position: int
    width: int
    height: int


class ArtworkCreate(BaseModel):
    title: Title
    technique: Technique
    width_cm: Dimension
    height_cm: Dimension
    depth_cm: Dimension | None = None
    year: int = Field(ge=1000, le=2100)
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    description: str | None = Field(default=None, max_length=4000)
    status: ArtworkStatus = ArtworkStatus.DRAFT


class ArtworkUpdate(BaseModel):
    """PATCH parcial: solo se aplican los campos enviados."""

    title: Title | None = None
    technique: Technique | None = None
    width_cm: Dimension | None = None
    height_cm: Dimension | None = None
    depth_cm: Dimension | None = None
    year: int | None = Field(default=None, ge=1000, le=2100)
    price: Decimal | None = Field(default=None, ge=0, max_digits=10, decimal_places=2)
    description: str | None = Field(default=None, max_length=4000)
    status: ArtworkStatus | None = None


class ArtworkListItem(BaseModel):
    id: int
    title: str
    technique: str
    width_cm: Decimal
    height_cm: Decimal
    year: int
    price: Decimal | None
    status: ArtworkStatus
    artist: ArtistSummary
    cover_thumb_url: str | None


class ArtworkDetail(BaseModel):
    id: int
    title: str
    technique: str
    width_cm: Decimal
    height_cm: Decimal
    depth_cm: Decimal | None
    year: int
    price: Decimal | None
    description: str | None
    status: ArtworkStatus
    artist: ArtistSummary
    images: list[ArtworkImageRead]
    created_at: datetime
    updated_at: datetime
