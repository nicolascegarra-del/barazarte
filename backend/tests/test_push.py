import json
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pywebpush import WebPushException
from sqlmodel import Session, select

from app.cli import generate_vapid_keys
from app.core.config import Settings, get_settings
from app.models import Artist, Inquiry, PushSubscription
from app.models.base import utcnow
from app.services import push_service
from tests.conftest import make_artist, make_artwork

PANEL = "/api/v1/panel"
ENDPOINT = "https://push.example.com/send/abc123"
SUBSCRIPTION = {"endpoint": ENDPOINT, "keys": {"p256dh": "clave-p256dh", "auth": "clave-auth"}}


def _make_inquiry(session: Session, artist: Artist, *, read: bool = False) -> Inquiry:
    assert artist.id is not None
    inquiry = Inquiry(
        artist_id=artist.id,
        artwork_title="Atardecer",
        name="Carlos",
        email="carlos@example.com",
        message="Me interesa este cuadro, quisiera conocer disponibilidad.",
        read_at=utcnow() if read else None,
    )
    session.add(inquiry)
    session.commit()
    session.refresh(inquiry)
    return inquiry


def _subscription(session: Session, artist: Artist, endpoint: str = ENDPOINT) -> PushSubscription:
    assert artist.id is not None
    subscription = PushSubscription(
        artist_id=artist.id, endpoint=endpoint, p256dh="clave-p256dh", auth="clave-auth"
    )
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    return subscription


@pytest.fixture
def push_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    """Configuracion con VAPID activo en los modulos que la leen."""
    settings = get_settings().model_copy(
        update={
            "vapid_public_key": "public-key-base64url",
            "vapid_private_key": "private-key-base64url",
            "vapid_subject": "mailto:admin@barazarte.test",
        }
    )
    monkeypatch.setattr("app.api.public.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.push_service.get_settings", lambda: settings)
    return settings


# ─── Consultas sin leer ─────────────────────────────────────────────────────────


def test_contador_cuando_hay_consultas_entonces_cuenta_solo_las_sin_leer_del_artista(
    client: TestClient, session: Session, artist: Artist, auth_headers: dict[str, str]
) -> None:
    other = make_artist(session, email="otra@example.com", name="Otra")
    _make_inquiry(session, artist)
    _make_inquiry(session, artist)
    _make_inquiry(session, artist, read=True)
    _make_inquiry(session, other)

    response = client.get(f"{PANEL}/inquiries/unread-count", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"count": 2}


def test_read_all_cuando_se_llama_entonces_marca_las_del_artista_y_no_las_ajenas(
    client: TestClient, session: Session, artist: Artist, auth_headers: dict[str, str]
) -> None:
    other = make_artist(session, email="otra@example.com", name="Otra")
    _make_inquiry(session, artist)
    other_inquiry = _make_inquiry(session, other)

    response = client.post(f"{PANEL}/inquiries/read-all", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"count": 0}
    assert client.get(f"{PANEL}/inquiries/unread-count", headers=auth_headers).json() == {
        "count": 0
    }
    session.refresh(other_inquiry)
    assert other_inquiry.read_at is None


def test_listado_cuando_hay_consultas_entonces_incluye_read_at(
    client: TestClient, session: Session, artist: Artist, auth_headers: dict[str, str]
) -> None:
    _make_inquiry(session, artist)

    items = client.get(f"{PANEL}/inquiries", headers=auth_headers).json()["items"]

    assert items[0]["read_at"] is None


def test_contador_cuando_no_hay_token_entonces_401(client: TestClient) -> None:
    assert client.get(f"{PANEL}/inquiries/unread-count").status_code == 401
    assert client.post(f"{PANEL}/inquiries/read-all").status_code == 401


# ─── Suscripciones ──────────────────────────────────────────────────────────────


def test_subscribe_cuando_es_nueva_entonces_204_y_se_guarda(
    client: TestClient, session: Session, artist: Artist, auth_headers: dict[str, str]
) -> None:
    response = client.post(f"{PANEL}/push/subscribe", json=SUBSCRIPTION, headers=auth_headers)

    assert response.status_code == 204
    stored = session.exec(select(PushSubscription)).one()
    assert (stored.artist_id, stored.endpoint, stored.p256dh) == (
        artist.id,
        ENDPOINT,
        "clave-p256dh",
    )


def test_subscribe_cuando_el_endpoint_existe_entonces_actualiza_y_reasigna(
    client: TestClient, session: Session, artist: Artist, auth_headers: dict[str, str]
) -> None:
    other = make_artist(session, email="otra@example.com", name="Otra")
    _subscription(session, other)
    body = {**SUBSCRIPTION, "keys": {"p256dh": "nueva-p256dh", "auth": "nueva-auth"}}

    response = client.post(f"{PANEL}/push/subscribe", json=body, headers=auth_headers)

    assert response.status_code == 204
    stored = session.exec(select(PushSubscription)).one()
    assert stored.artist_id == artist.id
    assert (stored.p256dh, stored.auth) == ("nueva-p256dh", "nueva-auth")


def test_subscribe_cuando_el_endpoint_no_es_https_entonces_422(
    client: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    body = {**SUBSCRIPTION, "endpoint": "http://push.example.com/send/abc123"}

    response = client.post(f"{PANEL}/push/subscribe", json=body, headers=auth_headers)

    assert response.status_code == 422
    assert response.json()["error"]["field"] == "endpoint"
    assert session.exec(select(PushSubscription)).all() == []


def test_subscribe_cuando_el_endpoint_es_demasiado_largo_entonces_422(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    body = {**SUBSCRIPTION, "endpoint": "https://push.example.com/" + "a" * 3000}

    response = client.post(f"{PANEL}/push/subscribe", json=body, headers=auth_headers)

    assert response.status_code == 422


def test_subscribe_cuando_no_hay_token_entonces_401(client: TestClient) -> None:
    assert client.post(f"{PANEL}/push/subscribe", json=SUBSCRIPTION).status_code == 401
    assert client.post(f"{PANEL}/push/unsubscribe", json={"endpoint": ENDPOINT}).status_code == 401


def test_unsubscribe_cuando_es_del_artista_entonces_204_y_se_borra(
    client: TestClient, session: Session, artist: Artist, auth_headers: dict[str, str]
) -> None:
    _subscription(session, artist)

    response = client.post(
        f"{PANEL}/push/unsubscribe", json={"endpoint": ENDPOINT}, headers=auth_headers
    )

    assert response.status_code == 204
    assert session.exec(select(PushSubscription)).all() == []


def test_unsubscribe_cuando_es_de_otro_artista_entonces_204_pero_no_se_borra(
    client: TestClient, session: Session, auth_headers: dict[str, str]
) -> None:
    other = make_artist(session, email="otra@example.com", name="Otra")
    _subscription(session, other)

    response = client.post(
        f"{PANEL}/push/unsubscribe", json={"endpoint": ENDPOINT}, headers=auth_headers
    )

    assert response.status_code == 204
    assert len(session.exec(select(PushSubscription)).all()) == 1


# ─── Clave publica ──────────────────────────────────────────────────────────────


def test_public_key_cuando_no_hay_configuracion_entonces_null(client: TestClient) -> None:
    response = client.get("/api/v1/push/public-key")

    assert response.status_code == 200
    assert response.json() == {"public_key": None}


def test_public_key_cuando_esta_configurada_entonces_la_devuelve(
    client: TestClient, push_settings: Settings
) -> None:
    response = client.get("/api/v1/push/public-key")

    assert response.json() == {"public_key": "public-key-base64url"}


# ─── Tarea de envio ─────────────────────────────────────────────────────────────


def test_envio_cuando_hay_suscripciones_entonces_envia_a_cada_una_con_payload(
    session: Session, artist: Artist, push_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(push_service, "webpush", lambda **kwargs: calls.append(kwargs))
    _subscription(session, artist, "https://push.example.com/a")
    _subscription(session, artist, "https://push.example.com/b")
    _make_inquiry(session, artist, read=True)
    inquiry = _make_inquiry(session, artist)
    assert inquiry.id is not None

    push_service.send_new_inquiry_push(session, inquiry.id)

    assert {call["subscription_info"]["endpoint"] for call in calls} == {
        "https://push.example.com/a",
        "https://push.example.com/b",
    }
    assert json.loads(calls[0]["data"]) == {
        "title": "Nueva consulta",
        "body": "Carlos pregunta por «Atardecer»",
        "url": "/panel/consultas",
        "unread": 1,
    }
    assert calls[0]["ttl"] == 86400
    assert calls[0]["vapid_claims"] == {"sub": "mailto:admin@barazarte.test"}
    assert calls[0]["vapid_private_key"] == "private-key-base64url"


def test_envio_cuando_la_respuesta_es_410_entonces_borra_la_suscripcion(
    session: Session, artist: Artist, push_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_webpush(**kwargs: Any) -> None:
        status = 410 if kwargs["subscription_info"]["endpoint"].endswith("/gone") else 201
        if status == 410:
            raise WebPushException("gone", response=SimpleNamespace(status_code=410))

    monkeypatch.setattr(push_service, "webpush", fake_webpush)
    _subscription(session, artist, "https://push.example.com/gone")
    _subscription(session, artist, "https://push.example.com/ok")
    inquiry = _make_inquiry(session, artist)
    assert inquiry.id is not None

    push_service.send_new_inquiry_push(session, inquiry.id)

    remaining = session.exec(select(PushSubscription)).all()
    assert [item.endpoint for item in remaining] == ["https://push.example.com/ok"]


def test_envio_cuando_falla_otro_error_entonces_conserva_la_suscripcion_y_sigue(
    session: Session, artist: Artist, push_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: list[str] = []

    def fake_webpush(**kwargs: Any) -> None:
        endpoint = kwargs["subscription_info"]["endpoint"]
        sent.append(endpoint)
        if endpoint.endswith("/fail"):
            raise WebPushException("boom", response=SimpleNamespace(status_code=500))

    monkeypatch.setattr(push_service, "webpush", fake_webpush)
    _subscription(session, artist, "https://push.example.com/fail")
    _subscription(session, artist, "https://push.example.com/ok")
    inquiry = _make_inquiry(session, artist)
    assert inquiry.id is not None

    push_service.send_new_inquiry_push(session, inquiry.id)

    assert len(sent) == 2
    assert len(session.exec(select(PushSubscription)).all()) == 2


def test_envio_cuando_no_hay_vapid_entonces_no_envia(
    session: Session, artist: Artist, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(push_service, "webpush", lambda **kwargs: calls.append(kwargs))
    _subscription(session, artist)
    inquiry = _make_inquiry(session, artist)
    assert inquiry.id is not None

    push_service.send_new_inquiry_push(session, inquiry.id)

    assert calls == []


# ─── Encolado al crear la consulta ──────────────────────────────────────────────


def test_consulta_cuando_se_crea_entonces_se_encola_la_tarea_push(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    pushed: list[int] = []
    monkeypatch.setattr("app.tasks.push.send_new_inquiry.delay", pushed.append)
    monkeypatch.setattr("app.tasks.email.send_artist_notification.delay", lambda _id: None)
    monkeypatch.setattr("app.tasks.email.send_buyer_confirmation.delay", lambda _id: None)
    artwork = make_artwork(session, make_artist(session))

    response = client.post(
        f"/api/v1/artworks/{artwork.id}/inquiries",
        json={
            "name": "Carlos",
            "email": "carlos@example.com",
            "message": "Me interesa este cuadro, quisiera conocer disponibilidad.",
            "accept_privacy": True,
        },
    )

    assert response.status_code == 202
    inquiry = session.exec(select(Inquiry)).one()
    assert inquiry.read_at is None
    assert pushed == [inquiry.id]


def test_consulta_cuando_honeypot_relleno_entonces_no_se_encola_push(
    client: TestClient, session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    pushed: list[int] = []
    monkeypatch.setattr("app.tasks.push.send_new_inquiry.delay", pushed.append)
    artwork = make_artwork(session, make_artist(session))

    client.post(
        f"/api/v1/artworks/{artwork.id}/inquiries",
        json={
            "name": "Bot",
            "email": "bot@example.com",
            "message": "Mensaje de spam suficientemente largo.",
            "accept_privacy": True,
            "website": "http://spam.test",
        },
    )

    assert pushed == []


# ─── CLI ────────────────────────────────────────────────────────────────────────


def test_generate_vapid_cuando_se_genera_entonces_formatos_compatibles() -> None:
    from py_vapid import Vapid

    public_key, private_key = generate_vapid_keys()

    assert len(public_key) == 87  # 65 bytes sin comprimir en base64url sin relleno
    assert Vapid.from_string(private_key).private_key is not None
