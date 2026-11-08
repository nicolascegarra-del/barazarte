"""Engine y sesiones de base de datos."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine
from sqlmodel import Session, create_engine

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True, echo=False)


def get_session() -> Iterator[Session]:
    """Dependencia FastAPI: una sesion por peticion."""
    with Session(get_engine()) as session:
        yield session
