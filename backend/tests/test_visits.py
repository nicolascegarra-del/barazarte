from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import ArtworkStatus, VisitDaily
from app.services.visit_service import today_utc
from tests.conftest import make_artist, make_artwork

TRACK_URL = "/api/v1/track"


def _counts(session: Session) -> dict[int, int]:
    session.expire_all()
    return {row.artwork_id: row.count for row in session.exec(select(VisitDaily))}


def test_track_cuando_obra_publicada_entonces_204_y_suma_al_contador_diario(
    client: TestClient, session: Session
) -> None:
    artwork = make_artwork(session, make_artist(session))

    for _ in range(3):
        response = client.post(TRACK_URL, json={"artwork_id": artwork.id})
        assert response.status_code == 204

    assert _counts(session) == {artwork.id: 3}
    row = session.exec(select(VisitDaily)).one()
    assert row.date == today_utc()


def test_track_cuando_artwork_id_es_null_o_ausente_entonces_cuenta_visita_general(
    client: TestClient, session: Session
) -> None:
    assert client.post(TRACK_URL, json={"artwork_id": None}).status_code == 204
    assert client.post(TRACK_URL, json={}).status_code == 204

    assert _counts(session) == {0: 2}


def test_track_cuando_obra_no_existe_borrador_o_artista_desactivado_entonces_204_sin_contar(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    draft = make_artwork(session, artist, "Borrador", ArtworkStatus.DRAFT)
    off_artist = make_artist(session, email="off@example.com", is_active=False)
    hidden = make_artwork(session, off_artist, "Oculta")

    for artwork_id in (9999, draft.id, hidden.id):
        assert client.post(TRACK_URL, json={"artwork_id": artwork_id}).status_code == 204

    assert _counts(session) == {}


def test_track_cuando_id_invalido_entonces_422(client: TestClient) -> None:
    assert client.post(TRACK_URL, json={"artwork_id": 0}).status_code == 422
    assert client.post(TRACK_URL, json={"artwork_id": "abc"}).status_code == 422


def test_track_cuando_se_supera_el_rate_limit_por_ip_entonces_429(client: TestClient) -> None:
    statuses = [client.post(TRACK_URL, json={}).status_code for _ in range(121)]

    assert statuses[:120] == [204] * 120
    assert statuses[120] == 429


def test_track_no_guarda_datos_personales(client: TestClient, session: Session) -> None:
    client.post(TRACK_URL, json={}, headers={"User-Agent": "Mozilla/5.0 secreto"})

    assert set(VisitDaily.model_fields) == {"date", "artwork_id", "count"}
