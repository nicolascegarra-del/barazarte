import smtplib
from email.message import EmailMessage
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import Artist, EmailSettings, Inquiry
from app.services import email_service
from tests.conftest import login_headers, make_artist

URL = "/api/v1/admin/email-settings"
BODY: dict[str, Any] = {
    "host": "smtp.example.com",
    "port": 587,
    "username": "mailer",
    "password": "s3cr3t-pass",
    "security": "starttls",
    "from_name": "BarazArte",
    "from_email": "hola@example.com",
}


@pytest.fixture
def admin_headers(client: TestClient, session: Session) -> dict[str, str]:
    make_artist(session, email="admin@example.com", name="Admin", is_admin=True)
    return login_headers(client, "admin@example.com")


class FakeSMTP:
    instances: list["FakeSMTP"] = []
    fail_with: Exception | None = None

    def __init__(self, host: str, port: int, timeout: float = 0, **_: Any) -> None:
        self.host, self.port, self.timeout = host, port, timeout
        self.calls: list[str] = []
        self.sent: list[EmailMessage] = []
        self.login_args: tuple[str, str] | None = None
        FakeSMTP.instances.append(self)

    def __enter__(self) -> "FakeSMTP":
        if FakeSMTP.fail_with is not None:
            raise FakeSMTP.fail_with
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def starttls(self, **_: Any) -> None:
        self.calls.append("starttls")

    def login(self, user: str, password: str) -> None:
        self.login_args = (user, password)

    def send_message(self, message: EmailMessage) -> None:
        self.sent.append(message)


@pytest.fixture
def fake_smtp(monkeypatch: pytest.MonkeyPatch) -> type[FakeSMTP]:
    FakeSMTP.instances = []
    FakeSMTP.fail_with = None
    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)
    return FakeSMTP


def test_endpoints_cuando_no_es_admin_entonces_403(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    assert client.get(URL, headers=auth_headers).status_code == 403
    assert client.put(URL, json=BODY, headers=auth_headers).status_code == 403
    assert client.post(f"{URL}/test", json={}, headers=auth_headers).status_code == 403
    assert client.get(URL).status_code == 401


def test_get_cuando_no_hay_fila_entonces_usa_entorno(
    client: TestClient, admin_headers: dict[str, str]
) -> None:
    data = client.get(URL, headers=admin_headers).json()
    assert data["source"] == "environment"
    assert data["has_password"] is False
    assert data["security"] == "none"
    assert data["from_email"] == "no-reply@barazarte.local"
    assert "password" not in data


def test_put_entonces_no_devuelve_password_y_la_cifra(
    client: TestClient, session: Session, admin_headers: dict[str, str]
) -> None:
    response = client.put(URL, json=BODY, headers=admin_headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["source"] == "database"
    assert data["has_password"] is True
    assert "s3cr3t-pass" not in response.text
    row = session.get(EmailSettings, 1)
    assert row is not None
    assert row.password_encrypted
    assert "s3cr3t-pass" not in row.password_encrypted
    assert client.get(URL, headers=admin_headers).json() == data


def test_put_password_ausente_conserva_y_vacia_borra(
    client: TestClient, session: Session, admin_headers: dict[str, str]
) -> None:
    client.put(URL, json=BODY, headers=admin_headers)
    session.expire_all()
    first = session.get(EmailSettings, 1)
    assert first is not None
    stored = first.password_encrypted

    without_password = {key: value for key, value in BODY.items() if key != "password"}
    data = client.put(URL, json=without_password | {"port": 465}, headers=admin_headers).json()
    session.expire_all()
    row = session.get(EmailSettings, 1)
    assert row is not None
    assert data["port"] == 465
    assert data["has_password"] is True
    assert row.password_encrypted == stored

    data = client.put(URL, json=BODY | {"password": None}, headers=admin_headers).json()
    assert data["has_password"] is True

    data = client.put(URL, json=BODY | {"password": ""}, headers=admin_headers).json()
    assert data["has_password"] is False


@pytest.mark.parametrize(
    "override",
    [
        {"port": 0},
        {"port": 70000},
        {"host": "smtp example.com"},
        {"host": "https://smtp.example.com"},
        {"from_email": "no-es-email"},
        {"security": "tls"},
        {"from_name": "A\nBcc: x@y.com"},
    ],
)
def test_put_cuando_datos_invalidos_entonces_422(
    client: TestClient, admin_headers: dict[str, str], override: dict[str, Any]
) -> None:
    assert client.put(URL, json=BODY | override, headers=admin_headers).status_code == 422


def test_test_send_entonces_envia_al_admin_con_la_config_de_bd(
    client: TestClient, admin_headers: dict[str, str], fake_smtp: type[FakeSMTP]
) -> None:
    client.put(URL, json=BODY, headers=admin_headers)
    response = client.post(f"{URL}/test", json={}, headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == {"status": "sent"}
    smtp = fake_smtp.instances[-1]
    assert (smtp.host, smtp.port, smtp.timeout) == ("smtp.example.com", 587, 10)
    assert smtp.calls == ["starttls"]
    assert smtp.login_args == ("mailer", "s3cr3t-pass")
    assert smtp.sent[0]["To"] == "admin@example.com"
    assert smtp.sent[0]["From"] == "BarazArte <hola@example.com>"


def test_test_send_con_destinatario_explicito(
    client: TestClient, admin_headers: dict[str, str], fake_smtp: type[FakeSMTP]
) -> None:
    response = client.post(f"{URL}/test", json={"to": "otro@example.com"}, headers=admin_headers)
    assert response.status_code == 200
    assert fake_smtp.instances[-1].sent[0]["To"] == "otro@example.com"


def test_test_send_cuando_smtp_falla_entonces_502(
    client: TestClient, admin_headers: dict[str, str], fake_smtp: type[FakeSMTP]
) -> None:
    client.put(URL, json=BODY, headers=admin_headers)
    fake_smtp.fail_with = smtplib.SMTPAuthenticationError(535, b"bad creds s3cr3t-pass")
    response = client.post(f"{URL}/test", json={}, headers=admin_headers)
    assert response.status_code == 502
    error = response.json()["error"]
    assert error["code"] == "EMAIL_SEND_FAILED"
    assert "contrasena" in error["message"]
    assert "s3cr3t-pass" not in response.text

    fake_smtp.fail_with = ConnectionRefusedError("refused")
    assert client.post(f"{URL}/test", headers=admin_headers).status_code == 502


def test_email_service_usa_bd_antes_que_entorno(
    client: TestClient,
    session: Session,
    admin_headers: dict[str, str],
    fake_smtp: type[FakeSMTP],
) -> None:
    message = EmailMessage()
    message["To"] = "x@example.com"
    message["Subject"] = "Hola"
    message.set_content("hola")

    email_service.send_email(message, session=session)
    assert fake_smtp.instances[-1].host == "localhost"  # sin fila: entorno

    client.put(URL, json=BODY, headers=admin_headers)
    email_service.send_email(message, session=session)
    assert fake_smtp.instances[-1].host == "smtp.example.com"


def test_reply_to_en_consulta_al_artista_es_el_comprador(artist: Artist) -> None:
    inquiry = Inquiry(
        artist_id=1,
        artwork_id=1,
        artwork_title="Mar",
        name="Ana",
        email="ana@example.com",
        message="Hola",
    )
    message = email_service.build_artist_notification(inquiry, artist)
    assert message["Reply-To"] == "ana@example.com"
