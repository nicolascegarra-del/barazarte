from pydantic import BaseModel, Field, field_validator

MAX_ENDPOINT_LENGTH = 2048


class PushKeys(BaseModel):
    p256dh: str = Field(min_length=1, max_length=256)
    auth: str = Field(min_length=1, max_length=256)


class PushSubscribe(BaseModel):
    endpoint: str = Field(min_length=10, max_length=MAX_ENDPOINT_LENGTH)
    keys: PushKeys

    @field_validator("endpoint")
    @classmethod
    def _require_https(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("El endpoint debe usar https.")
        return value


class PushUnsubscribe(BaseModel):
    endpoint: str = Field(min_length=1, max_length=MAX_ENDPOINT_LENGTH)


class PushPublicKey(BaseModel):
    public_key: str | None
