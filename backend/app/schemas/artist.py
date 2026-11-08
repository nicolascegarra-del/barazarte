from pydantic import BaseModel


class ArtistSummary(BaseModel):
    id: int
    display_name: str


class ArtistPublic(ArtistSummary):
    bio: str | None
    website: str | None
