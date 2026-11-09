from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field, StringConstraints, field_validator

from app.models.enums import InquiryStatus

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Phone = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=30, pattern=r"^[0-9+()\-\s.]*$")
]
Message = Annotated[str, StringConstraints(strip_whitespace=True, min_length=10, max_length=2000)]


class InquiryCreate(BaseModel):
    name: Name
    email: EmailStr
    phone: Phone | None = None
    message: Message
    accept_privacy: bool = Field(description="Aceptacion de la politica de privacidad (RGPD)")
    # Honeypot: campo oculto en el formulario que los humanos dejan vacio
    website: str = Field(default="", max_length=200)

    @field_validator("accept_privacy")
    @classmethod
    def _must_accept(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Debes aceptar la politica de privacidad.")
        return value

    @field_validator("phone")
    @classmethod
    def _empty_phone_to_none(cls, value: str | None) -> str | None:
        return value or None


class InquiryAccepted(BaseModel):
    status: Literal["received"] = "received"


class InquiryRead(BaseModel):
    id: int
    artwork_id: int | None
    artwork_title: str
    name: str
    email: str
    phone: str | None
    message: str
    status: InquiryStatus
    created_at: datetime
    read_at: datetime | None


class InquiryStatusUpdate(BaseModel):
    status: InquiryStatus


class UnreadCount(BaseModel):
    count: int
