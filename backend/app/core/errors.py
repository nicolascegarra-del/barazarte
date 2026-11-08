"""Errores de dominio y handlers con el formato estandar Klyp.

Formato: {"error": {"code": "...", "message": "...", "field": "...", "request_id": "..."}}
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

_HTTP_STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
}


class AppError(Exception):
    """Error esperado de negocio (validacion, not found, permisos...)."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        field: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.field = field
        self.headers = headers


def not_found(message: str = "Recurso no encontrado.") -> AppError:
    return AppError(404, "NOT_FOUND", message)


def unauthorized(message: str = "Credenciales no validas.") -> AppError:
    return AppError(401, "UNAUTHORIZED", message, headers={"WWW-Authenticate": "Bearer"})


def forbidden(message: str = "No tienes permiso para realizar esta accion.") -> AppError:
    return AppError(403, "FORBIDDEN", message)


def error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    field: str | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, str] = {"code": code, "message": message}
    if field:
        body["field"] = field
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        body["request_id"] = request_id
    return JSONResponse({"error": body}, status_code=status_code, headers=headers)


async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return error_response(request, exc.status_code, exc.code, exc.message, exc.field, exc.headers)


async def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0]
    # loc[0] es "body"/"query"/"path": no aporta al cliente
    field = ".".join(str(part) for part in first["loc"][1:]) or None
    # Nunca se devuelve el valor recibido (podria ser sensible)
    return error_response(request, 422, "VALIDATION_ERROR", str(first["msg"]), field)


async def _handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _HTTP_STATUS_CODES.get(exc.status_code, "HTTP_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "Error en la peticion."
    return error_response(request, exc.status_code, code, message, headers=exc.headers)


async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        "Error no controlado en %s %s (request_id=%s)",
        request.method,
        request.url.path,
        request_id,
        exc_info=exc,
    )
    return error_response(request, 500, "INTERNAL_ERROR", "Error interno del servidor.")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_unexpected)
