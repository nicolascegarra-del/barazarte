from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import Artist, ArtworkStatus, Inquiry, InquiryStatus, VisitDaily
from app.models.base import utcnow
from app.services.visit_service import today_utc
from tests.conftest import login_headers, make_artist, make_artwork

ADMIN_EMAIL = "admin@example.com"

ARTWORK_BODY = {
    "title": "Mar",
    "technique": "Acuarela",
    "width_cm": "40",
    "height_cm": "30",
    "year": 2023,
}


@pytest.fixture
def admin(session: Session) -> Artist:
    return make_artist(session, email=ADMIN_EMAIL, name="Admin", is_admin=True, max_artworks=None)


@pytest.fixture
def admin_headers(client: TestClient, admin: Artist) -> dict[str, str]:
    return login_headers(client, ADMIN_EMAIL)


@pytest.fixture
def account_emails(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, int]]:
    calls: list[tuple[str, int]] = []
    monkeypatch.setattr(
        "app.services.account_service.enqueue_account_email",
        lambda kind, artist_id: calls.append((kind, artist_id)),
    )
    return calls


def _create(client: TestClient, headers: dict[str, str]) -> int:
    return client.post("/api/v1/panel/artworks", json=ARTWORK_BODY, headers=headers).status_code


def _add_inquiry(session: Session, artist: Artist, status: InquiryStatus) -> None:
    assert artist.id is not None
    session.add(
        Inquiry(
            artist_id=artist.id,
            artwork_title="Obra",
            name="Comprador",
            email="c@example.com",
            message="Me interesa mucho esta obra",
            status=status,
        )
    )
    session.commit()


# ─── Limite de obras ─────────────────────────────────────────────────────────────


def test_crear_obra_cuando_se_alcanza_el_limite_con_borradores_entonces_409(
    client: TestClient, session: Session
) -> None:
    make_artist(session, max_artworks=2)
    headers = login_headers(client)
    assert (
        client.post("/api/v1/panel/artworks", json=ARTWORK_BODY, headers=headers).status_code == 201
    )
    assert (
        client.post("/api/v1/panel/artworks", json=ARTWORK_BODY, headers=headers).status_code == 201
    )

    response = client.post("/api/v1/panel/artworks", json=ARTWORK_BODY, headers=headers)

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "ARTWORK_LIMIT_REACHED"
    assert "limite" in error["message"]


def test_crear_obra_cuando_limite_es_null_entonces_no_hay_tope(
    client: TestClient, session: Session
) -> None:
    make_artist(session, max_artworks=None)
    headers = login_headers(client)

    for _ in range(7):
        response = client.post("/api/v1/panel/artworks", json=ARTWORK_BODY, headers=headers)
        assert response.status_code == 201


def test_crear_obra_cuando_se_borra_una_entonces_vuelve_a_haber_cupo(
    client: TestClient, session: Session
) -> None:
    make_artist(session, max_artworks=1)
    headers = login_headers(client)
    created = client.post("/api/v1/panel/artworks", json=ARTWORK_BODY, headers=headers)
    assert (
        client.post("/api/v1/panel/artworks", json=ARTWORK_BODY, headers=headers).status_code == 409
    )

    client.delete(f"/api/v1/panel/artworks/{created.json()['id']}", headers=headers)

    assert (
        client.post("/api/v1/panel/artworks", json=ARTWORK_BODY, headers=headers).status_code == 201
    )


# ─── Artistas desactivados ocultos ───────────────────────────────────────────────


def test_publico_cuando_el_artista_esta_desactivado_entonces_sus_obras_y_perfil_desaparecen(
    client: TestClient, session: Session
) -> None:
    active = make_artist(session, email="a@example.com", name="Activa")
    disabled = make_artist(session, email="d@example.com", name="Inactiva")
    visible = make_artwork(session, active, "Visible")
    hidden = make_artwork(session, disabled, "Oculta")
    disabled.is_active = False
    session.add(disabled)
    session.commit()

    listing = client.get("/api/v1/artworks").json()
    by_artist = client.get("/api/v1/artworks", params={"artist_id": disabled.id}).json()

    assert [item["title"] for item in listing["items"]] == ["Visible"]
    assert listing["total"] == 1
    assert by_artist["total"] == 0
    assert client.get(f"/api/v1/artworks/{visible.id}").status_code == 200
    assert client.get(f"/api/v1/artworks/{hidden.id}").status_code == 404
    assert client.get(f"/api/v1/artists/{disabled.id}").status_code == 404


def test_consulta_cuando_la_obra_es_de_un_artista_desactivado_entonces_404(
    client: TestClient, session: Session, enqueued: list[int]
) -> None:
    artist = make_artist(session, is_active=False)
    artwork = make_artwork(session, artist)

    response = client.post(
        f"/api/v1/artworks/{artwork.id}/inquiries",
        json={
            "name": "Ana",
            "email": "ana@example.com",
            "message": "Me interesa esta obra, gracias",
            "accept_privacy": True,
        },
    )

    assert response.status_code == 404
    assert enqueued == []


# ─── Permisos admin ──────────────────────────────────────────────────────────────


def test_admin_cuando_no_hay_token_entonces_401(client: TestClient) -> None:
    assert client.get("/api/v1/admin/stats").status_code == 401


def test_admin_cuando_el_artista_no_es_admin_entonces_403_en_todos_los_endpoints(
    client: TestClient, artist: Artist, auth_headers: dict[str, str]
) -> None:
    calls = [
        client.get("/api/v1/admin/stats", headers=auth_headers),
        client.get("/api/v1/admin/artists", headers=auth_headers),
        client.patch(f"/api/v1/admin/artists/{artist.id}", json={}, headers=auth_headers),
        client.post(f"/api/v1/admin/artists/{artist.id}/reset-password", headers=auth_headers),
    ]

    for response in calls:
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FORBIDDEN"


def test_admin_cuando_es_admin_entonces_200_y_me_lo_indica(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    assert client.get("/api/v1/admin/stats", headers=admin_headers).status_code == 200
    me = client.get("/api/v1/auth/me", headers=admin_headers).json()
    assert me["is_admin"] is True
    assert me["max_artworks"] is None


# ─── Stats ───────────────────────────────────────────────────────────────────────


def test_stats_cuando_hay_datos_entonces_agrega_artistas_obras_consultas_y_visitas(
    client: TestClient, session: Session, admin: Artist, admin_headers: dict[str, str]
) -> None:
    maria = make_artist(session, email="m@example.com")
    make_artist(session, email="off@example.com", is_active=False)
    make_artist(session, email="nov@example.com", email_verified=False)
    published = make_artwork(session, maria, "P1")
    make_artwork(session, maria, "P2")
    make_artwork(session, maria, "B", ArtworkStatus.DRAFT)
    make_artwork(session, maria, "R", ArtworkStatus.RESERVED)
    make_artwork(session, maria, "V", ArtworkStatus.SOLD)
    _add_inquiry(session, maria, InquiryStatus.NEW)
    _add_inquiry(session, maria, InquiryStatus.NEW)
    _add_inquiry(session, maria, InquiryStatus.CONTACTED)
    today = today_utc()
    session.add(VisitDaily(date=today, artwork_id=published.id or 0, count=4))
    session.add(VisitDaily(date=today, artwork_id=0, count=1))
    session.add(VisitDaily(date=today - timedelta(days=29), artwork_id=0, count=2))
    session.add(VisitDaily(date=today - timedelta(days=45), artwork_id=0, count=10))
    session.commit()

    body = client.get("/api/v1/admin/stats", headers=admin_headers).json()

    assert body["artists"] == {"total": 4, "active": 3, "disabled": 1, "unverified": 1}
    assert body["artworks"] == {
        "total": 5,
        "borrador": 1,
        "publicado": 2,
        "reservado": 1,
        "vendido": 1,
    }
    assert body["inquiries"] == {"total": 3, "nueva": 2, "contactado": 1, "vendida": 0}
    assert body["visits"]["total"] == 17
    assert body["visits"]["last_30_days"] == 7
    by_day = body["visits"]["by_day"]
    assert len(by_day) == 30
    assert by_day[-1] == {"date": today.isoformat(), "count": 5}
    assert by_day[0] == {"date": (today - timedelta(days=29)).isoformat(), "count": 2}
    assert by_day[1]["count"] == 0


def test_stats_cuando_no_hay_datos_entonces_ceros_y_30_dias(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    body = client.get("/api/v1/admin/stats", headers=admin_headers).json()

    assert body["artworks"]["total"] == 0
    assert body["visits"]["total"] == 0
    assert len(body["visits"]["by_day"]) == 30


# ─── Listado de artistas ─────────────────────────────────────────────────────────


def test_listado_artistas_cuando_hay_actividad_entonces_incluye_contadores(
    client: TestClient, session: Session, admin: Artist, admin_headers: dict[str, str]
) -> None:
    maria = make_artist(session, email="m@example.com", name="Maria Lopez")
    published = make_artwork(session, maria, "P1")
    make_artwork(session, maria, "B", ArtworkStatus.DRAFT)
    _add_inquiry(session, maria, InquiryStatus.NEW)
    session.add(VisitDaily(date=today_utc(), artwork_id=published.id or 0, count=3))
    session.add(VisitDaily(date=today_utc(), artwork_id=0, count=9))
    session.commit()

    body = client.get("/api/v1/admin/artists", headers=admin_headers).json()

    assert body["total"] == 2
    row = next(item for item in body["items"] if item["email"] == "m@example.com")
    assert row == {
        "id": maria.id,
        "email": "m@example.com",
        "display_name": "Maria Lopez",
        "is_active": True,
        "email_verified": True,
        "is_admin": False,
        "max_artworks": 5,
        "artworks_count": 2,
        "published_count": 1,
        "inquiries_count": 1,
        "visits_count": 3,
        "created_at": row["created_at"],
    }
    assert "password_hash" not in row


def test_listado_artistas_cuando_se_busca_y_pagina_entonces_filtra_por_nombre_o_email(
    client: TestClient, session: Session, admin_headers: dict[str, str]
) -> None:
    make_artist(session, email="uno@example.com", name="Carmen Ruiz")
    make_artist(session, email="dos@example.com", name="Pedro")
    make_artist(session, email="carmela@example.com", name="Otro")

    by_name = client.get("/api/v1/admin/artists", params={"q": "ruiz"}, headers=admin_headers)
    by_email = client.get("/api/v1/admin/artists", params={"q": "CARMEL"}, headers=admin_headers)
    wildcard = client.get("/api/v1/admin/artists", params={"q": "%"}, headers=admin_headers)
    paged = client.get(
        "/api/v1/admin/artists", params={"page": 2, "page_size": 2}, headers=admin_headers
    )

    assert [item["email"] for item in by_name.json()["items"]] == ["uno@example.com"]
    assert [item["email"] for item in by_email.json()["items"]] == ["carmela@example.com"]
    assert wildcard.json()["total"] == 0
    assert paged.json()["total"] == 4
    assert len(paged.json()["items"]) == 2


# ─── PATCH artista ───────────────────────────────────────────────────────────────


def test_patch_cuando_se_desactiva_y_cambia_limite_entonces_se_aplican(
    client: TestClient, session: Session, admin_headers: dict[str, str]
) -> None:
    maria = make_artist(session, email="m@example.com")

    response = client.patch(
        f"/api/v1/admin/artists/{maria.id}",
        json={"is_active": False, "max_artworks": 20},
        headers=admin_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_active"] is False
    assert body["max_artworks"] == 20


def test_patch_cuando_max_artworks_es_null_entonces_ilimitado_y_ausente_no_cambia(
    client: TestClient, session: Session, admin_headers: dict[str, str]
) -> None:
    maria = make_artist(session, email="m@example.com", max_artworks=5)
    url = f"/api/v1/admin/artists/{maria.id}"

    only_active = client.patch(url, json={"is_active": True}, headers=admin_headers)
    unlimited = client.patch(url, json={"max_artworks": None}, headers=admin_headers)

    assert only_active.json()["max_artworks"] == 5
    assert unlimited.json()["max_artworks"] is None


def test_patch_cuando_limite_negativo_o_is_active_null_entonces_error(
    client: TestClient, session: Session, admin_headers: dict[str, str]
) -> None:
    maria = make_artist(session, email="m@example.com")
    url = f"/api/v1/admin/artists/{maria.id}"

    negative = client.patch(url, json={"max_artworks": -1}, headers=admin_headers)
    null_active = client.patch(url, json={"is_active": None}, headers=admin_headers)

    assert negative.status_code == 422
    assert null_active.status_code == 422


def test_patch_cuando_el_admin_se_desactiva_a_si_mismo_entonces_409(
    client: TestClient, admin: Artist, admin_headers: dict[str, str]
) -> None:
    response = client.patch(
        f"/api/v1/admin/artists/{admin.id}", json={"is_active": False}, headers=admin_headers
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CANNOT_DISABLE_SELF"


def test_patch_cuando_el_objetivo_es_otro_admin_entonces_403(
    client: TestClient, session: Session, admin_headers: dict[str, str]
) -> None:
    other = make_artist(session, email="otro-admin@example.com", is_admin=True)

    response = client.patch(
        f"/api/v1/admin/artists/{other.id}", json={"is_active": False}, headers=admin_headers
    )

    assert response.status_code == 403


def test_patch_cuando_el_artista_no_existe_entonces_404(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    response = client.patch("/api/v1/admin/artists/9999", json={}, headers=admin_headers)

    assert response.status_code == 404


def test_patch_cuando_se_baja_el_limite_por_debajo_de_las_obras_entonces_no_borra_pero_bloquea(
    client: TestClient, session: Session, admin_headers: dict[str, str]
) -> None:
    maria = make_artist(session, email="m@example.com", max_artworks=10)
    make_artwork(session, maria, "A")
    make_artwork(session, maria, "B")

    client.patch(
        f"/api/v1/admin/artists/{maria.id}", json={"max_artworks": 1}, headers=admin_headers
    )

    headers = login_headers(client, "m@example.com")
    assert client.get("/api/v1/panel/artworks", headers=headers).json()["total"] == 2
    response = client.post("/api/v1/panel/artworks", json=ARTWORK_BODY, headers=headers)
    assert response.status_code == 409


# ─── Reset desde admin ───────────────────────────────────────────────────────────


def test_admin_reset_cuando_artista_activo_entonces_202_y_encola_email_de_reset(
    client: TestClient,
    session: Session,
    admin_headers: dict[str, str],
    account_emails: list[tuple[str, int]],
) -> None:
    maria = make_artist(session, email="m@example.com")

    response = client.post(
        f"/api/v1/admin/artists/{maria.id}/reset-password", headers=admin_headers
    )

    assert response.status_code == 202
    assert account_emails == [("password_reset", maria.id)]


def test_admin_reset_cuando_artista_desactivado_o_admin_ajeno_o_inexistente_entonces_error(
    client: TestClient,
    session: Session,
    admin_headers: dict[str, str],
    account_emails: list[tuple[str, int]],
) -> None:
    disabled = make_artist(session, email="d@example.com", is_active=False)
    other_admin = make_artist(session, email="oa@example.com", is_admin=True)

    statuses = [
        client.post(
            f"/api/v1/admin/artists/{target}/reset-password", headers=admin_headers
        ).status_code
        for target in (disabled.id, other_admin.id, 9999)
    ]

    assert statuses == [409, 403, 404]
    assert account_emails == []


def test_tareas_de_email_cuando_se_importan_entonces_estan_registradas() -> None:
    from app.tasks import email as tasks

    assert tasks.send_verification_email.name == "accounts.send_verification_email"
    assert tasks.send_password_reset_email.name == "accounts.send_password_reset_email"
    assert tasks.send_account_exists_email.name == "accounts.send_account_exists_email"


def test_tabla_de_artistas_cuando_se_crea_por_defecto_entonces_usa_el_limite_de_la_config(
    session: Session,
) -> None:
    artist = Artist(email="x@example.com", password_hash="h", display_name="X", created_at=utcnow())
    session.add(artist)
    session.commit()

    stored = session.exec(select(Artist).where(Artist.email == "x@example.com")).one()
    assert stored.max_artworks == 5
    assert stored.email_verified is False
    assert stored.is_admin is False
