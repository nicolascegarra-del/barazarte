"""Filtros, facetas, vecinas e imagen para compartir del catalogo publico."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image
from sqlmodel import Session

from app.models import Artist, Artwork, ArtworkImage, ArtworkStatus
from tests.conftest import FakeStorage, make_artist

BASE_DATE = datetime(2025, 1, 1, tzinfo=UTC)


def add_artwork(
    session: Session,
    artist: Artist,
    title: str,
    *,
    technique: str = "Oleo",
    width: int = 30,
    height: int = 40,
    price: str | None = None,
    status: ArtworkStatus = ArtworkStatus.PUBLISHED,
    age_days: int = 0,
) -> Artwork:
    """Crea una obra; `age_days` mayor = mas antigua (orden 'recientes' determinista)."""
    assert artist.id is not None
    artwork = Artwork(
        artist_id=artist.id,
        title=title,
        technique=technique,
        width_cm=Decimal(width),
        height_cm=Decimal(height),
        year=2024,
        price=Decimal(price) if price is not None else None,
        status=status,
        created_at=BASE_DATE - timedelta(days=age_days),
    )
    session.add(artwork)
    session.commit()
    session.refresh(artwork)
    return artwork


def titles(client: TestClient, **params: object) -> list[str]:
    response = client.get("/api/v1/artworks", params=params)
    assert response.status_code == 200, response.text
    return [item["title"] for item in response.json()["items"]]


# ─── Filtros ────────────────────────────────────────────────────────────────────


def test_filtro_tecnica_cuando_difiere_en_mayusculas_entonces_coincide(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    add_artwork(session, artist, "A", technique="Acuarela")
    add_artwork(session, artist, "B", technique="Oleo", age_days=1)

    assert titles(client, technique="aCUARELA") == ["A"]


def test_filtro_tecnica_cuando_es_parcial_entonces_no_coincide(
    client: TestClient, session: Session
) -> None:
    add_artwork(session, make_artist(session), "A", technique="Acuarela")

    assert titles(client, technique="Acuar") == []


def test_filtro_precio_cuando_se_usa_entonces_excluye_obras_sin_precio(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    add_artwork(session, artist, "Sin precio", price=None)
    add_artwork(session, artist, "Barata", price="100", age_days=1)
    add_artwork(session, artist, "Cara", price="900.50", age_days=2)

    assert titles(client, min_price=0) == ["Barata", "Cara"]
    assert titles(client, max_price=1000) == ["Barata", "Cara"]
    assert titles(client, min_price=100, max_price=100) == ["Barata"]
    assert titles(client, min_price="200.5") == ["Cara"]


def test_filtro_tamano_cuando_se_evaluan_limites_entonces_usa_lado_mayor(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    add_artwork(session, artist, "p49", width=49, height=10)
    add_artwork(session, artist, "m50", width=20, height=50, age_days=1)
    add_artwork(session, artist, "m100", width=100, height=100, age_days=2)
    add_artwork(session, artist, "g101", width=101, height=5, age_days=3)

    assert titles(client, size="pequeno") == ["p49"]
    assert titles(client, size="mediano") == ["m50", "m100"]
    assert titles(client, size="grande") == ["g101"]


def test_filtro_disponible_cuando_es_true_entonces_solo_publicadas(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    add_artwork(session, artist, "Libre")
    add_artwork(session, artist, "Reservada", status=ArtworkStatus.RESERVED, age_days=1)
    add_artwork(session, artist, "Vendida", status=ArtworkStatus.SOLD, age_days=2)

    assert titles(client, available="true") == ["Libre"]
    assert titles(client, available="false") == ["Libre", "Reservada", "Vendida"]


def test_filtros_combinados_cuando_se_aplican_varios_entonces_se_intersectan(
    client: TestClient, session: Session
) -> None:
    maria, luis = make_artist(session), make_artist(session, "luis@example.com", "Luis")
    add_artwork(session, maria, "Ok", technique="Oleo", width=120, price="500")
    add_artwork(session, maria, "Pequena", technique="Oleo", width=20, price="500", age_days=1)
    add_artwork(session, luis, "Otro artista", technique="Oleo", width=120, price="500", age_days=2)
    add_artwork(session, maria, "Cara", technique="Oleo", width=120, price="5000", age_days=3)

    result = titles(
        client,
        artist_id=maria.id,
        technique="oleo",
        size="grande",
        max_price=1000,
        available="true",
    )

    assert result == ["Ok"]


def test_orden_precio_cuando_hay_obras_sin_precio_entonces_van_al_final(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    add_artwork(session, artist, "Nula", price=None)
    add_artwork(session, artist, "Media", price="200", age_days=1)
    add_artwork(session, artist, "Alta", price="300", age_days=2)
    add_artwork(session, artist, "Baja", price="100", age_days=3)

    assert titles(client, sort="precio_asc") == ["Baja", "Media", "Alta", "Nula"]
    assert titles(client, sort="precio_desc") == ["Alta", "Media", "Baja", "Nula"]


def test_orden_por_defecto_cuando_no_se_indica_entonces_es_recientes(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    add_artwork(session, artist, "Vieja", age_days=5)
    add_artwork(session, artist, "Nueva", age_days=0)

    assert titles(client) == ["Nueva", "Vieja"]
    assert titles(client, sort="recientes") == ["Nueva", "Vieja"]


def test_filtros_cuando_el_valor_es_invalido_entonces_422(client: TestClient) -> None:
    for params in (
        {"sort": "azar"},
        {"size": "enorme"},
        {"min_price": -1},
        {"max_price": "abc"},
        {"available": "quizas"},
        {"technique": ""},
    ):
        response = client.get("/api/v1/artworks", params=params)
        assert response.status_code == 422, params
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# ─── Facetas ────────────────────────────────────────────────────────────────────


def test_facetas_cuando_hay_obras_entonces_cuentan_solo_las_visibles(
    client: TestClient, session: Session
) -> None:
    maria = make_artist(session, name="Maria")
    luis = make_artist(session, "luis@example.com", "Luis")
    baja = make_artist(session, "baja@example.com", "Baja", is_active=False)
    add_artwork(session, maria, "A", technique="Oleo", price="100")
    add_artwork(session, maria, "B", technique="Oleo", price="300", age_days=1)
    add_artwork(session, luis, "C", technique="Acuarela", price=None, age_days=2)
    add_artwork(session, maria, "Borrador", technique="Grabado", status=ArtworkStatus.DRAFT)
    add_artwork(session, baja, "De baja", technique="Grabado", price="9999")

    response = client.get("/api/v1/artworks/facets")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert body["techniques"] == [
        {"name": "Oleo", "count": 2},
        {"name": "Acuarela", "count": 1},
    ]
    assert body["artists"] == [
        {"id": maria.id, "display_name": "Maria", "count": 2},
        {"id": luis.id, "display_name": "Luis", "count": 1},
    ]
    assert Decimal(body["price"]["min"]) == 100
    assert Decimal(body["price"]["max"]) == 300
    assert isinstance(body["price"]["min"], str)


def test_facetas_cuando_no_hay_obras_entonces_vacias_y_precio_nulo(client: TestClient) -> None:
    response = client.get("/api/v1/artworks/facets")

    assert response.json() == {
        "techniques": [],
        "artists": [],
        "price": {"min": None, "max": None},
        "total": 0,
    }


# ─── Vecinas ────────────────────────────────────────────────────────────────────


def test_vecinas_cuando_la_obra_es_intermedia_entonces_devuelve_prev_y_next(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    newest = add_artwork(session, artist, "Nueva", age_days=0)
    middle = add_artwork(session, artist, "Media", age_days=1)
    oldest = add_artwork(session, artist, "Vieja", age_days=2)
    add_artwork(session, artist, "Oculta", status=ArtworkStatus.DRAFT, age_days=1)

    body = client.get(f"/api/v1/artworks/{middle.id}/neighbors").json()

    assert body == {
        "prev": {"id": newest.id, "title": "Nueva"},
        "next": {"id": oldest.id, "title": "Vieja"},
    }


def test_vecinas_cuando_es_primera_o_ultima_entonces_un_lado_es_nulo(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    first = add_artwork(session, artist, "Primera", age_days=0)
    last = add_artwork(session, artist, "Ultima", age_days=1)

    first_body = client.get(f"/api/v1/artworks/{first.id}/neighbors").json()
    last_body = client.get(f"/api/v1/artworks/{last.id}/neighbors").json()

    assert first_body == {"prev": None, "next": {"id": last.id, "title": "Ultima"}}
    assert last_body == {"prev": {"id": first.id, "title": "Primera"}, "next": None}


def test_vecinas_cuando_hay_misma_fecha_entonces_desempata_por_id(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    older_id = add_artwork(session, artist, "Id bajo")
    newer_id = add_artwork(session, artist, "Id alto")

    body = client.get(f"/api/v1/artworks/{older_id.id}/neighbors").json()

    assert body["prev"]["id"] == newer_id.id
    assert body["next"] is None


def test_vecinas_cuando_la_obra_no_es_visible_entonces_404(
    client: TestClient, session: Session
) -> None:
    draft = add_artwork(session, make_artist(session), "Borrador", status=ArtworkStatus.DRAFT)

    assert client.get(f"/api/v1/artworks/{draft.id}/neighbors").status_code == 404
    assert client.get("/api/v1/artworks/9999/neighbors").status_code == 404


# ─── Imagen para compartir ──────────────────────────────────────────────────────


def add_image(
    session: Session,
    storage: FakeStorage,
    artwork: Artwork,
    *,
    position: int = 0,
    size: tuple[int, int] = (800, 1000),
    color: tuple[int, int, int] = (200, 30, 30),
    store: bool = True,
) -> ArtworkImage:
    assert artwork.id is not None
    key = f"artworks/{artwork.id}/img{position}.webp"
    if store:
        buffer = BytesIO()
        Image.new("RGB", size, color).save(buffer, format="WEBP")
        storage.put(key, buffer.getvalue(), "image/webp")
    image = ArtworkImage(
        artwork_id=artwork.id,
        storage_key=key,
        thumb_key=f"{key}.thumb",
        position=position,
        width=size[0],
        height=size[1],
    )
    session.add(image)
    session.commit()
    session.refresh(image)
    return image


def test_og_cuando_la_obra_tiene_imagen_entonces_jpeg_1200x630_cacheado(
    client: TestClient, session: Session, storage: FakeStorage
) -> None:
    artwork = add_artwork(session, make_artist(session), "Con imagen")
    image = add_image(session, storage, artwork)

    response = client.get(f"/api/v1/artworks/{artwork.id}/og.jpg")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.headers["cache-control"] == "public, max-age=86400"
    assert len(response.content) < 300 * 1024
    rendered = Image.open(BytesIO(response.content))
    assert rendered.format == "JPEG"
    assert rendered.size == (1200, 630)
    # Esquina: fondo marfil; centro: la obra (rojiza), sin recortar
    corner = rendered.getpixel((5, 5))
    assert all(abs(a - b) <= 3 for a, b in zip(corner, (0xFA, 0xF8, 0xF4), strict=True))
    center = rendered.getpixel((600, 315))
    assert center[0] > 150 and center[1] < 90
    assert f"og/{artwork.id}-{image.id}.jpg" in storage.objects


def test_og_cuando_ya_esta_cacheada_entonces_se_sirve_sin_regenerar(
    client: TestClient, session: Session, storage: FakeStorage
) -> None:
    artwork = add_artwork(session, make_artist(session), "Cacheada")
    image = add_image(session, storage, artwork)
    storage.objects[f"og/{artwork.id}-{image.id}.jpg"] = b"JPEG-CACHEADO"
    storage.objects.pop(image.storage_key)  # si regenerase, fallaria con 404

    response = client.get(f"/api/v1/artworks/{artwork.id}/og.jpg")

    assert response.status_code == 200
    assert response.content == b"JPEG-CACHEADO"


def test_og_cuando_cambia_la_imagen_principal_entonces_cambia_la_clave_de_cache(
    client: TestClient, session: Session, storage: FakeStorage
) -> None:
    artwork = add_artwork(session, make_artist(session), "Dos imagenes")
    first = add_image(session, storage, artwork, position=0)
    client.get(f"/api/v1/artworks/{artwork.id}/og.jpg")
    # La segunda se crea antes de borrar la primera: SQLite reutilizaria el id liberado
    second = add_image(session, storage, artwork, position=1, color=(20, 20, 200))
    session.delete(first)
    session.commit()

    response = client.get(f"/api/v1/artworks/{artwork.id}/og.jpg")

    assert response.status_code == 200
    assert f"og/{artwork.id}-{second.id}.jpg" in storage.objects
    center = Image.open(BytesIO(response.content)).getpixel((600, 315))
    assert center[2] > 150


def test_og_cuando_la_obra_no_es_visible_entonces_404(
    client: TestClient, session: Session, storage: FakeStorage
) -> None:
    draft = add_artwork(session, make_artist(session), "Borrador", status=ArtworkStatus.DRAFT)
    add_image(session, storage, draft)

    assert client.get(f"/api/v1/artworks/{draft.id}/og.jpg").status_code == 404
    assert client.get("/api/v1/artworks/9999/og.jpg").status_code == 404


def test_og_cuando_no_hay_imagen_entonces_404(client: TestClient, session: Session) -> None:
    artwork = add_artwork(session, make_artist(session), "Sin imagen")

    response = client.get(f"/api/v1/artworks/{artwork.id}/og.jpg")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_og_cuando_falta_el_objeto_de_origen_entonces_404(
    client: TestClient, session: Session, storage: FakeStorage
) -> None:
    artwork = add_artwork(session, make_artist(session), "Origen perdido")
    add_image(session, storage, artwork, store=False)

    assert client.get(f"/api/v1/artworks/{artwork.id}/og.jpg").status_code == 404


def test_og_cuando_el_origen_esta_corrupto_entonces_404(
    client: TestClient, session: Session, storage: FakeStorage
) -> None:
    artwork = add_artwork(session, make_artist(session), "Corrupta")
    image = add_image(session, storage, artwork, store=False)
    storage.objects[image.storage_key] = b"no-es-una-imagen"

    assert client.get(f"/api/v1/artworks/{artwork.id}/og.jpg").status_code == 404
