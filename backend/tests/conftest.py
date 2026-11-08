import os
from collections.abc import Iterator

# La configuracion debe fijarse antes de importar la app
os.environ.update(
    {
        "APP_ENV": "test",
        "DATABASE_URL": "sqlite://",
        "JWT_SECRET_KEY": "test-secret-key-test-secret-key-0123456789",
        "RATE_LIMIT_BACKEND": "memory",
        "COOKIE_SECURE": "false",
        "BCRYPT_ROUNDS": "4",
        "MINIO_PUBLIC_BASE_URL": "http://minio.test",
        "MINIO_BUCKET_NAME": "test-bucket",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from app.core.database import get_session  # noqa: E402
from app.core.rate_limit import get_rate_limiter  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.core.storage import get_storage  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Artist, Artwork, ArtworkStatus  # noqa: E402

ARTIST_PASSWORD = "clave-segura-123"


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = data

    def delete(self, key: str) -> None:
        self.objects.pop(key, None)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session


@pytest.fixture
def storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture
def enqueued(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Sustituye el encolado Celery por una lista de ids de consultas."""
    calls: list[int] = []
    monkeypatch.setattr(
        "app.services.inquiry_service.enqueue_inquiry_emails",
        lambda inquiry_id: calls.append(inquiry_id),
    )
    return calls


@pytest.fixture
def client(session: Session, storage: FakeStorage) -> Iterator[TestClient]:
    get_rate_limiter.cache_clear()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_storage] = lambda: storage
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_artist(
    session: Session,
    email: str = "maria@example.com",
    name: str = "Maria",
    *,
    is_admin: bool = False,
    is_active: bool = True,
    email_verified: bool = True,
    max_artworks: int | None = 5,
) -> Artist:
    artist = Artist(
        email=email,
        password_hash=hash_password(ARTIST_PASSWORD),
        display_name=name,
        is_admin=is_admin,
        is_active=is_active,
        email_verified=email_verified,
        max_artworks=max_artworks,
    )
    session.add(artist)
    session.commit()
    session.refresh(artist)
    return artist


def make_artwork(
    session: Session,
    artist: Artist,
    title: str = "Atardecer",
    status: ArtworkStatus = ArtworkStatus.PUBLISHED,
) -> Artwork:
    assert artist.id is not None
    artwork = Artwork(
        artist_id=artist.id,
        title=title,
        technique="Oleo sobre lienzo",
        width_cm=50,
        height_cm=70,
        year=2024,
        status=status,
    )
    session.add(artwork)
    session.commit()
    session.refresh(artwork)
    return artwork


def login_headers(client: TestClient, email: str = "maria@example.com") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": ARTIST_PASSWORD})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def artist(session: Session) -> Artist:
    return make_artist(session)


@pytest.fixture
def auth_headers(client: TestClient, artist: Artist) -> dict[str, str]:
    return login_headers(client)
