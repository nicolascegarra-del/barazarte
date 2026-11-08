from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_BYTES = 72  # limite de bcrypt


def _check_password_bytes(value: str) -> str:
    if len(value.encode()) > MAX_PASSWORD_BYTES:
        raise ValueError(f"La contrasena no puede superar {MAX_PASSWORD_BYTES} bytes.")
    return value


NewPassword = Annotated[
    str,
    Field(min_length=MIN_PASSWORD_LENGTH, max_length=128),
    AfterValidator(_check_password_bytes),
]
DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: DisplayName
    password: NewPassword
    accept_privacy: bool = Field(description="Aceptacion de la politica de privacidad (RGPD)")

    @field_validator("accept_privacy")
    @classmethod
    def _must_accept(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Debes aceptar la politica de privacidad.")
        return value


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1, max_length=2048)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=1, max_length=2048)
    new_password: NewPassword


class Accepted(BaseModel):
    status: Literal["received"] = "received"


class ArtistPrivate(BaseModel):
    id: int
    email: str
    display_name: str
    bio: str | None
    website: str | None
    is_admin: bool
    max_artworks: int | None = Field(description="Limite de obras; null = ilimitado")
    artworks_count: int = Field(description="Obras del artista, incluidos borradores")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int = Field(description="Segundos de validez del access token")
    artist: ArtistPrivate
