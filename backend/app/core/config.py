"""Configuracion de la aplicacion leida de variables de entorno."""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "barazarte-api"
    app_env: str = "development"
    debug: bool = False
    docs_enabled: bool = True
    frontend_base_url: str = "http://localhost:3000"
    cors_origins: str = "http://localhost:3000"
    trust_proxy_headers: bool = False

    database_url: str = "postgresql+psycopg://barazarte:barazarte@localhost:5432/barazarte"
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_backend: str = Field(default="redis", pattern="^(redis|memory)$")

    jwt_secret_key: str = ""
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7
    bcrypt_rounds: int = Field(default=12, ge=4, le=16)
    cookie_secure: bool = True

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_bucket_name: str = "barazarte"
    minio_secure: bool = False
    minio_public_base_url: str = "http://localhost:9000"
    max_upload_bytes: int = 10 * 1024 * 1024
    max_images_per_artwork: int = 10

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_starttls: bool = False
    mail_from: str = "BarazArte <no-reply@barazarte.local>"

    inquiry_rate_limit: int = 5
    inquiry_rate_window_seconds: int = 3600
    login_rate_limit: int = 10
    login_rate_window_seconds: int = 60

    @model_validator(mode="after")
    def _validate_security(self) -> "Settings":
        if len(self.jwt_secret_key) < MIN_SECRET_LENGTH:
            raise ValueError(f"JWT_SECRET_KEY obligatorio, minimo {MIN_SECRET_LENGTH} caracteres")
        if self.app_env == "production" and (self.bcrypt_rounds < 12 or not self.cookie_secure):
            raise ValueError(
                "En production BCRYPT_ROUNDS >= 12 y COOKIE_SECURE=true son obligatorios"
            )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
