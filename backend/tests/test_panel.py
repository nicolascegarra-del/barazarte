from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session

from app.models import Artist, ArtworkStatus, Inquiry
from tests.conftest import FakeStorage, login_headers, make_artist, make_artwork

ARTWORK_BODY = {
    "title": "  Mar en calma ",
    "technique": "Acuarela",
    "width_cm": "40.5",
    "height_cm": "30",
    "year": 2023,
    "price": "850.00",
}


def _png_bytes(size: tuple[int, int] = (800, 600)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, "navy").save(buffer, format="PNG")
    return buffer.getvalue()


def _create_artwork(client: TestClient, headers: dict[str, str]) -> int:
    response = client.post("/api/v1/panel/artworks", json=ARTWORK_BODY, headers=headers)
    assert response.status_code == 201, response.text
    return int(response.json()["id"])


def _upload(client: TestClient, headers: dict[str, str], artwork_id: int, data: bytes, mime: str):
    return client.post(
        f"/api/v1/panel/artworks/{artwork_id}/images",
        headers=headers,
        files={"file": ("cuadro.bin", data, mime)},
        data={"alt_text": "Vista frontal"},
    )


def test_crear_obra_cuando_datos_validos_entonces_queda_en_borrador_con_titulo_limpio(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post("/api/v1/panel/artworks", json=ARTWORK_BODY, headers=auth_headers)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Mar en calma"
    assert body["status"] == "borrador"


def test_crear_obra_cuando_nace_publicada_entonces_409(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post(
        "/api/v1/panel/artworks", json={**ARTWORK_BODY, "status": "publicado"}, headers=auth_headers
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ARTWORK_NEEDS_IMAGE"


def test_obra_ajena_cuando_otro_artista_intenta_editarla_entonces_404(
    client: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    other = make_artist(session, "otro@example.com", "Otro")
    foreign = make_artwork(session, other)

    response = client.patch(
        f"/api/v1/panel/artworks/{foreign.id}", json={"title": "Robada"}, headers=auth_headers
    )

    assert response.status_code == 404


def test_listado_panel_cuando_hay_obras_ajenas_entonces_solo_devuelve_las_propias(
    client: TestClient, session: Session, artist: Artist, auth_headers: dict[str, str]
) -> None:
    make_artwork(session, artist, "Mia", ArtworkStatus.DRAFT)
    make_artwork(session, make_artist(session, "otro@example.com", "Otro"), "Ajena")

    response = client.get("/api/v1/panel/artworks", headers=auth_headers)

    assert [item["title"] for item in response.json()["items"]] == ["Mia"]


def test_flujo_imagen_cuando_se_sube_png_entonces_guarda_webp_y_miniatura_y_permite_publicar(
    client: TestClient, auth_headers: dict[str, str], storage: FakeStorage
) -> None:
    artwork_id = _create_artwork(client, auth_headers)

    upload = _upload(client, auth_headers, artwork_id, _png_bytes(), "image/png")

    assert upload.status_code == 201, upload.text
    body = upload.json()
    assert body["url"].startswith("http://minio.test/test-bucket/artworks/")
    assert body["url"].endswith(".webp")
    assert body["thumb_url"].endswith("_thumb.webp")
    assert len(storage.objects) == 2

    publish = client.patch(
        f"/api/v1/panel/artworks/{artwork_id}", json={"status": "publicado"}, headers=auth_headers
    )
    assert publish.status_code == 200
    assert client.get(f"/api/v1/artworks/{artwork_id}").status_code == 200


def test_publicar_cuando_no_hay_imagenes_entonces_409(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    artwork_id = _create_artwork(client, auth_headers)

    response = client.patch(
        f"/api/v1/panel/artworks/{artwork_id}", json={"status": "publicado"}, headers=auth_headers
    )

    assert response.status_code == 409


def test_subida_cuando_mime_no_permitido_entonces_415(
    client: TestClient, auth_headers: dict[str, str], storage: FakeStorage
) -> None:
    artwork_id = _create_artwork(client, auth_headers)

    response = _upload(client, auth_headers, artwork_id, b"<?php echo 1;", "text/plain")

    assert response.status_code == 415
    assert storage.objects == {}


def test_subida_cuando_contenido_no_es_imagen_aunque_mime_diga_png_entonces_422(
    client: TestClient, auth_headers: dict[str, str], storage: FakeStorage
) -> None:
    artwork_id = _create_artwork(client, auth_headers)

    response = _upload(client, auth_headers, artwork_id, b"esto no es un png", "image/png")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_IMAGE"
    assert storage.objects == {}


def test_borrar_obra_cuando_tiene_imagenes_entonces_se_eliminan_de_storage(
    client: TestClient, auth_headers: dict[str, str], storage: FakeStorage
) -> None:
    artwork_id = _create_artwork(client, auth_headers)
    _upload(client, auth_headers, artwork_id, _png_bytes(), "image/png")

    response = client.delete(f"/api/v1/panel/artworks/{artwork_id}", headers=auth_headers)

    assert response.status_code == 204
    assert storage.objects == {}


def test_consultas_cuando_el_artista_cambia_el_estado_entonces_se_persiste(
    client: TestClient, session: Session, artist: Artist, auth_headers: dict[str, str]
) -> None:
    artwork = make_artwork(session, artist)
    inquiry = Inquiry(
        artist_id=artist.id or 0,
        artwork_id=artwork.id,
        artwork_title=artwork.title,
        name="Carlos",
        email="c@example.com",
        message="Hola, me interesa la obra.",
    )
    session.add(inquiry)
    session.commit()
    session.refresh(inquiry)

    listing = client.get("/api/v1/panel/inquiries", headers=auth_headers)
    patch = client.patch(
        f"/api/v1/panel/inquiries/{inquiry.id}", json={"status": "contactado"}, headers=auth_headers
    )

    assert listing.json()["total"] == 1
    assert patch.status_code == 200
    assert patch.json()["status"] == "contactado"


def test_consultas_cuando_pertenecen_a_otro_artista_entonces_404_al_cambiar_estado(
    client: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    other = make_artist(session, "otro@example.com", "Otro")
    artwork = make_artwork(session, other)
    inquiry = Inquiry(
        artist_id=other.id or 0,
        artwork_id=artwork.id,
        artwork_title=artwork.title,
        name="Carlos",
        email="c@example.com",
        message="Hola, me interesa la obra.",
    )
    session.add(inquiry)
    session.commit()
    session.refresh(inquiry)

    response = client.patch(
        f"/api/v1/panel/inquiries/{inquiry.id}", json={"status": "vendida"}, headers=auth_headers
    )

    assert response.status_code == 404
    assert login_headers(client)  # el artista original sigue autenticado
