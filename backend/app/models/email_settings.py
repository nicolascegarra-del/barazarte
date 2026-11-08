from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from app.models.base import utcnow

EMAIL_SETTINGS_ID = 1


class EmailSettings(SQLModel, table=True):
    """Cuenta SMTP unica de la plataforma (singleton: siempre id=1).

    La contrasena se guarda cifrada (Fernet) y nunca se devuelve por la API."""

    __tablename__ = "email_settings"

    id: int = Field(default=EMAIL_SETTINGS_ID, primary_key=True)
    host: str = Field(max_length=255)
    port: int
    username: str | None = Field(default=None, max_length=255)
    password_encrypted: str | None = Field(default=None)
    security: str = Field(max_length=10)  # none | starttls | ssl
    from_name: str = Field(max_length=100)
    from_email: str = Field(max_length=254)
    updated_at: datetime = Field(
        default_factory=utcnow, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
