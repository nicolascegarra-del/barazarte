from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.security import (
    JWT_ALGORITHM,
    PurposeToken,
    TokenType,
    create_purpose_token,
    create_token,
)
from app.models import Artist
from app.services import email_service, token_service
from tests.conftest import ARTIST_PASSWORD, make_artist

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
VERIFY_URL = "/api/v1/auth/verify-email"
RESET_REQUEST_URL = "/api/v1/auth/password-reset/request"
RESET_CONFIRM_URL = "/api/v1/auth/password-reset/confirm"

NEW_PASSWORD = "otra-clave-segura-456"

REGISTER_BODY = {
    "email": "Nueva@Example.com",
    "display_name": "  Nueva Artista ",
    "password": "una-clave-larga-1",
    "accept_privacy": True,
}


@pytest.fixture
def account_emails(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, int]]:
    """Sustituye el encolado Celery por una lista de (tipo, id de artista)."""
    calls: list[tuple[str, int]] = []
    monkeypatch.setattr(
        "app.services.account_service.enqueue_account_email",
        lambda kind, artist_id: calls.append((kind, artist_id)),
    )
    return calls


def _get_artist(session: Session, email: str) -> Artist:
    artist = session.exec(select(Artist).where(Artist.email == email)).first()
    assert artist is not None
    return artist


# ─── Registro y verificacion ─────────────────────────────────────────────────────


def test_registro_cuando_datos_validos_entonces_202_cuenta_sin_verificar_y_email_encolado(
    client: TestClient, session: Session, account_emails: list[tuple[str, int]]
) -> None:
    response = client.post(REGISTER_URL, json=REGISTER_BODY)

    assert response.status_code == 202
    assert response.json() == {"status": "received"}
    artist = _get_artist(session, "nueva@example.com")
    assert artist.display_name == "Nueva Artista"
    assert artist.email_verified is False
    assert artist.is_active is True
    assert artist.is_admin is False
    assert artist.max_artworks == get_settings().default_max_artworks == 5
    assert artist.id is not None
    assert account_emails == [("verification", artist.id)]


def test_registro_cuando_email_ya_existe_entonces_misma_respuesta_y_email_ya_tienes_cuenta(
    client: TestClient, session: Session, account_emails: list[tuple[str, int]]
) -> None:
    existing = make_artist(session, email="nueva@example.com")

    response = client.post(REGISTER_URL, json=REGISTER_BODY)

    assert response.status_code == 202
    assert response.json() == {"status": "received"}
    assert account_emails == [("account_exists", existing.id)]
    assert len(list(session.exec(select(Artist)))) == 1


@pytest.mark.parametrize(
    ("override", "field"),
    [
        ({"password": "corta"}, "password"),
        ({"accept_privacy": False}, "accept_privacy"),
        ({"email": "no-es-email"}, "email"),
        ({"display_name": "   "}, "display_name"),
    ],
)
def test_registro_cuando_datos_invalidos_entonces_422(
    client: TestClient, override: dict[str, object], field: str
) -> None:
    response = client.post(REGISTER_URL, json={**REGISTER_BODY, **override})

    assert response.status_code == 422
    assert response.json()["error"]["field"] == field


def test_registro_cuando_se_supera_el_rate_limit_entonces_429(
    client: TestClient, account_emails: list[tuple[str, int]]
) -> None:
    for index in range(5):
        client.post(REGISTER_URL, json={**REGISTER_BODY, "email": f"a{index}@example.com"})

    response = client.post(REGISTER_URL, json=REGISTER_BODY)

    assert response.status_code == 429


def test_verificar_email_cuando_token_valido_entonces_204_y_ya_puede_iniciar_sesion(
    client: TestClient, session: Session, account_emails: list[tuple[str, int]]
) -> None:
    client.post(REGISTER_URL, json=REGISTER_BODY)
    artist = _get_artist(session, "nueva@example.com")
    token = token_service.create_verification_token(artist)

    blocked = client.post(LOGIN_URL, json={"email": artist.email, "password": "una-clave-larga-1"})
    verified = client.post(VERIFY_URL, json={"token": token})
    allowed = client.post(LOGIN_URL, json={"email": artist.email, "password": "una-clave-larga-1"})

    assert blocked.status_code == 403
    assert verified.status_code == 204
    assert allowed.status_code == 200
    assert allowed.json()["artist"]["max_artworks"] == 5


def test_verificar_email_cuando_token_ya_usado_entonces_400(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session, email_verified=False)
    token = token_service.create_verification_token(artist)

    first = client.post(VERIFY_URL, json={"token": token})
    second = client.post(VERIFY_URL, json={"token": token})

    assert first.status_code == 204
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "INVALID_TOKEN"


def test_verificar_email_cuando_token_caducado_entonces_400(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session, email_verified=False)
    assert artist.id is not None
    token = create_purpose_token(artist.id, PurposeToken.EMAIL_VERIFY, timedelta(hours=-1))

    response = client.post(VERIFY_URL, json={"token": token})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_TOKEN"


def test_verificar_email_cuando_token_es_basura_o_de_otro_tipo_entonces_400(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session, email_verified=False)
    assert artist.id is not None
    access = create_token(artist.id, TokenType.ACCESS)
    reset = token_service.create_password_reset_token(artist)

    for token in ("basura", access, reset):
        response = client.post(VERIFY_URL, json={"token": token})
        assert response.status_code == 400, token


def test_token_de_verificacion_cuando_se_usa_como_access_entonces_401(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session, email_verified=False)
    token = token_service.create_verification_token(artist)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401


def test_token_de_verificacion_cuando_se_firma_con_otra_clave_entonces_400(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session, email_verified=False)
    forged = jwt.encode(
        {
            "sub": str(artist.id),
            "type": "email_verify",
            "exp": datetime.now(UTC) + timedelta(hours=1),
        },
        "otra-clave-distinta-otra-clave-distinta",
        algorithm=JWT_ALGORITHM,
    )

    response = client.post(VERIFY_URL, json={"token": forged})

    assert response.status_code == 400


def test_email_de_verificacion_cuando_se_construye_entonces_incluye_el_enlace_del_frontend(
    session: Session,
) -> None:
    artist = make_artist(session, email_verified=False)

    message = email_service.build_verification_email(artist, "TOKEN123")

    body = message.get_content()
    assert f"{get_settings().frontend_base_url}/verificar-email?token=TOKEN123" in body
    assert message["To"] == artist.email


# ─── Login bloqueado ─────────────────────────────────────────────────────────────


def test_login_cuando_cuenta_desactivada_y_clave_correcta_entonces_403_account_disabled(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session, is_active=False)

    response = client.post(LOGIN_URL, json={"email": artist.email, "password": ARTIST_PASSWORD})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_DISABLED"


def test_login_cuando_email_sin_verificar_y_clave_correcta_entonces_403_email_not_verified(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session, email_verified=False)

    response = client.post(LOGIN_URL, json={"email": artist.email, "password": ARTIST_PASSWORD})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


def test_login_cuando_cuenta_bloqueada_y_clave_incorrecta_entonces_401_sin_filtrar_estado(
    client: TestClient, session: Session
) -> None:
    disabled = make_artist(session, email="d@example.com", is_active=False)
    unverified = make_artist(session, email="u@example.com", email_verified=False)

    for artist in (disabled, unverified):
        response = client.post(LOGIN_URL, json={"email": artist.email, "password": "mala"})
        assert response.status_code == 401


def test_token_vigente_cuando_se_deshabilita_al_artista_entonces_deja_de_valer(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    login = client.post(LOGIN_URL, json={"email": artist.email, "password": ARTIST_PASSWORD})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200

    artist.is_active = False
    session.add(artist)
    session.commit()

    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    assert client.get("/api/v1/panel/artworks", headers=headers).status_code == 401
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_me_cuando_hay_obras_entonces_devuelve_contador_limite_e_is_admin(
    client: TestClient, session: Session
) -> None:
    from tests.conftest import login_headers, make_artwork

    artist = make_artist(session, max_artworks=3)
    make_artwork(session, artist, "Una")
    make_artwork(session, artist, "Dos")

    response = client.get("/api/v1/auth/me", headers=login_headers(client))

    body = response.json()
    assert body["artworks_count"] == 2
    assert body["max_artworks"] == 3
    assert body["is_admin"] is False


# ─── Reset de contrasena ─────────────────────────────────────────────────────────


def test_reset_solicitar_cuando_cuenta_existe_entonces_202_y_email_encolado(
    client: TestClient, session: Session, account_emails: list[tuple[str, int]]
) -> None:
    artist = make_artist(session)

    response = client.post(RESET_REQUEST_URL, json={"email": artist.email.upper()})

    assert response.status_code == 202
    assert account_emails == [("password_reset", artist.id)]


def test_reset_solicitar_cuando_cuenta_no_existe_o_esta_desactivada_entonces_202_sin_email(
    client: TestClient, session: Session, account_emails: list[tuple[str, int]]
) -> None:
    disabled = make_artist(session, is_active=False)

    unknown = client.post(RESET_REQUEST_URL, json={"email": "nadie@example.com"})
    off = client.post(RESET_REQUEST_URL, json={"email": disabled.email})

    assert unknown.status_code == off.status_code == 202
    assert unknown.json() == off.json() == {"status": "received"}
    assert account_emails == []


def test_reset_confirmar_cuando_token_valido_entonces_204_y_cambia_la_clave(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    token = token_service.create_password_reset_token(artist)

    response = client.post(RESET_CONFIRM_URL, json={"token": token, "new_password": NEW_PASSWORD})

    assert response.status_code == 204
    old = client.post(LOGIN_URL, json={"email": artist.email, "password": ARTIST_PASSWORD})
    new = client.post(LOGIN_URL, json={"email": artist.email, "password": NEW_PASSWORD})
    assert old.status_code == 401
    assert new.status_code == 200


def test_reset_confirmar_cuando_token_ya_usado_entonces_400(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    token = token_service.create_password_reset_token(artist)

    first = client.post(RESET_CONFIRM_URL, json={"token": token, "new_password": NEW_PASSWORD})
    second = client.post(
        RESET_CONFIRM_URL, json={"token": token, "new_password": "tercera-clave-789"}
    )

    assert first.status_code == 204
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "INVALID_TOKEN"


def test_reset_confirmar_cuando_token_caducado_o_de_otro_tipo_entonces_400(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    assert artist.id is not None
    expired = create_purpose_token(
        artist.id,
        PurposeToken.PASSWORD_RESET,
        timedelta(minutes=-1),
        fingerprint="x",
    )
    verification = token_service.create_verification_token(artist)

    for token in (expired, verification, create_token(artist.id, TokenType.ACCESS)):
        response = client.post(
            RESET_CONFIRM_URL, json={"token": token, "new_password": NEW_PASSWORD}
        )
        assert response.status_code == 400


def test_reset_confirmar_cuando_clave_nueva_corta_entonces_422(
    client: TestClient, session: Session
) -> None:
    artist = make_artist(session)
    token = token_service.create_password_reset_token(artist)

    response = client.post(RESET_CONFIRM_URL, json={"token": token, "new_password": "corta"})

    assert response.status_code == 422


def test_email_de_reset_cuando_se_construye_entonces_incluye_el_enlace_restablecer(
    session: Session,
) -> None:
    artist = make_artist(session)

    message = email_service.build_password_reset_email(artist, "TOK")

    assert f"{get_settings().frontend_base_url}/restablecer?token=TOK" in message.get_content()
