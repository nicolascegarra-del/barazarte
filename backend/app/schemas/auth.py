from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ArtistPrivate(BaseModel):
    id: int
    email: str
    display_name: str
    bio: str | None
    website: str | None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int = Field(description="Segundos de validez del access token")
    artist: ArtistPrivate
