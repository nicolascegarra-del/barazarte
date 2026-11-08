from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import ArtworkStatus, Inquiry
from tests.conftest import make_artist, make_artwork

VALID_BODY = {
    "name": "Carlos",
    "email": "Carlos@Example.com",
    "message": "Me interesa este cuadro, quisiera conocer disponibilidad.",
    "accept_privacy": True,
}


def _url(artwork_id: int | None) -> str:
    return f"/api/v1/artworks/{artwork_id}/inquiries"


def test_consulta_cuando_es_valida_entonces_se_guarda_y_se_encolan_emails(
    client: TestClient, session: Session, enqueued: list[int]
) -> None:
    artwork = make_artwork(session, make_artist(session))

    response = client.post(_url(artwork.id), json=VALID_BODY)

    assert response.status_code == 202
    inquiry = session.exec(select(Inquiry)).one()
    assert inquiry.email == "carlos@example.com"
    assert inquiry.artwork_title == artwork.title
    assert inquiry.artist_id == artwork.artist_id
    assert enqueued == [inquiry.id]


def test_consulta_cuando_honeypot_relleno_entonces_responde_igual_pero_no_guarda(
    client: TestClient, session: Session, enqueued: list[int]
) -> None:
    artwork = make_artwork(session, make_artist(session))

    response = client.post(_url(artwork.id), json={**VALID_BODY, "website": "http://spam.test"})

    assert response.status_code == 202
    assert session.exec(select(Inquiry)).all() == []
    assert enqueued == []


def test_consulta_cuando_no_acepta_privacidad_entonces_422(
    client: TestClient, session: Session, enqueued: list[int]
) -> None:
    artwork = make_artwork(session, make_artist(session))

    response = client.post(_url(artwork.id), json={**VALID_BODY, "accept_privacy": False})

    assert response.status_code == 422
    assert response.json()["error"]["field"] == "accept_privacy"


def test_consulta_cuando_email_invalido_entonces_422(
    client: TestClient, session: Session, enqueued: list[int]
) -> None:
    artwork = make_artwork(session, make_artist(session))

    response = client.post(_url(artwork.id), json={**VALID_BODY, "email": "no-es-email"})

    assert response.status_code == 422
    assert response.json()["error"]["field"] == "email"


def test_consulta_cuando_la_obra_es_borrador_entonces_404(
    client: TestClient, session: Session, enqueued: list[int]
) -> None:
    artwork = make_artwork(session, make_artist(session), status=ArtworkStatus.DRAFT)

    response = client.post(_url(artwork.id), json=VALID_BODY)

    assert response.status_code == 404
    assert enqueued == []


def test_consulta_cuando_se_supera_el_rate_limit_entonces_429(
    client: TestClient, session: Session, enqueued: list[int]
) -> None:
    artwork = make_artwork(session, make_artist(session))

    statuses = [client.post(_url(artwork.id), json=VALID_BODY).status_code for _ in range(6)]

    assert statuses == [202] * 5 + [429]
