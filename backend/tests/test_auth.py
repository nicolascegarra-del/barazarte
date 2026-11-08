from fastapi.testclient import TestClient

from app.core.security import TokenType, create_token
from app.models import Artist
from tests.conftest import ARTIST_PASSWORD

LOGIN_URL = "/api/v1/auth/login"


def test_login_cuando_credenciales_validas_entonces_devuelve_token_y_cookie_segura(
    client: TestClient, artist: Artist
) -> None:
    response = client.post(LOGIN_URL, json={"email": artist.email, "password": ARTIST_PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 15 * 60
    assert "password_hash" not in body["artist"]
    cookie = response.headers["set-cookie"].lower()
    assert "refresh_token=" in cookie
    assert "httponly" in cookie
    assert "samesite=strict" in cookie
    assert "max-age=604800" in cookie


def test_login_cuando_password_incorrecta_entonces_401_con_formato_klyp(
    client: TestClient, artist: Artist
) -> None:
    response = client.post(LOGIN_URL, json={"email": artist.email, "password": "incorrecta"})

    assert response.status_code == 401
    error = response.json()["error"]
    assert error["code"] == "UNAUTHORIZED"
    assert error["request_id"].startswith("req_")


def test_login_cuando_email_desconocido_entonces_mismo_mensaje_que_password_incorrecta(
    client: TestClient, artist: Artist
) -> None:
    unknown = client.post(LOGIN_URL, json={"email": "nadie@example.com", "password": "x"})
    wrong = client.post(LOGIN_URL, json={"email": artist.email, "password": "x"})

    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json()["error"]["message"] == wrong.json()["error"]["message"]


def test_login_cuando_se_supera_el_rate_limit_entonces_429(client: TestClient) -> None:
    for _ in range(10):
        client.post(LOGIN_URL, json={"email": "a@example.com", "password": "x"})

    response = client.post(LOGIN_URL, json={"email": "a@example.com", "password": "x"})

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "RATE_LIMITED"
    assert "retry-after" in response.headers


def test_refresh_cuando_hay_cookie_valida_entonces_emite_nuevo_access_token(
    client: TestClient, artist: Artist
) -> None:
    client.post(LOGIN_URL, json={"email": artist.email, "password": ARTIST_PASSWORD})

    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_refresh_cuando_no_hay_cookie_entonces_401(client: TestClient) -> None:
    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 401


def test_me_cuando_se_usa_un_refresh_token_como_access_entonces_401(
    client: TestClient, artist: Artist
) -> None:
    assert artist.id is not None
    refresh = create_token(artist.id, TokenType.REFRESH)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {refresh}"})

    assert response.status_code == 401


def test_panel_cuando_no_hay_token_entonces_401(client: TestClient) -> None:
    response = client.get("/api/v1/panel/artworks")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
