from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import ArtworkStatus
from tests.conftest import make_artist, make_artwork


def test_listado_publico_cuando_hay_borradores_entonces_no_se_exponen(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    make_artwork(session, artist, "Visible")
    make_artwork(session, artist, "Oculta", ArtworkStatus.DRAFT)
    make_artwork(session, artist, "Vendida", ArtworkStatus.SOLD)

    response = client.get("/api/v1/artworks")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert {item["title"] for item in body["items"]} == {"Visible", "Vendida"}


def test_listado_publico_cuando_se_pagina_entonces_respeta_page_size(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    for index in range(5):
        make_artwork(session, artist, f"Obra {index}")

    response = client.get("/api/v1/artworks", params={"page": 2, "page_size": 2})

    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["pages"] == 3


def test_listado_publico_cuando_page_size_excede_maximo_entonces_422(client: TestClient) -> None:
    response = client.get("/api/v1/artworks", params={"page_size": 500})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_listado_publico_cuando_se_filtra_por_borrador_entonces_422(client: TestClient) -> None:
    response = client.get("/api/v1/artworks", params={"status": "borrador"})

    assert response.status_code == 422


def test_detalle_cuando_la_obra_es_borrador_entonces_404(
    client: TestClient, session: Session
) -> None:
    artwork = make_artwork(session, make_artist(session), status=ArtworkStatus.DRAFT)

    response = client.get(f"/api/v1/artworks/{artwork.id}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_detalle_cuando_la_obra_esta_publicada_entonces_incluye_artista(
    client: TestClient, session: Session
) -> None:
    artwork = make_artwork(session, make_artist(session, name="Maria"))

    response = client.get(f"/api/v1/artworks/{artwork.id}")

    assert response.status_code == 200
    assert response.json()["artist"]["display_name"] == "Maria"


def test_artista_publico_cuando_existe_entonces_no_expone_email(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)

    response = client.get(f"/api/v1/artists/{artist.id}")

    assert response.status_code == 200
    assert "email" not in response.json()
    assert "password_hash" not in response.json()
