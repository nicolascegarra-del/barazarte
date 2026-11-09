"""CORS: el navegador hace un preflight OPTIONS antes de peticiones que no son GET/POST simples."""

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _methods_in_use() -> set[str]:
    """Métodos HTTP de las rutas de la API, leídos del esquema OpenAPI."""
    paths = create_app().openapi()["paths"]
    return {m.upper() for operations in paths.values() for m in operations if m in HTTP_METHODS}


def test_cors_cuando_la_api_usa_put_y_delete_entonces_el_esquema_los_incluye() -> None:
    methods = _methods_in_use()

    assert {"GET", "POST", "PUT", "PATCH", "DELETE"} <= methods


def test_cors_cuando_una_ruta_usa_un_metodo_entonces_el_preflight_lo_permite(
    client: TestClient,
) -> None:
    origin = get_settings().cors_origin_list[0]

    for method in sorted(_methods_in_use()):
        response = client.options(
            "/api/v1/artworks",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )

        assert response.status_code == 200, f"El preflight de {method} es rechazado por CORS"
        assert response.headers["access-control-allow-origin"] == origin
