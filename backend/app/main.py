"""Punto de entrada de la API BarazArte."""

import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, panel, public
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.storage import MinioStorage, get_storage

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Respeta dependency_overrides para que los tests no intenten conectar con MinIO
    storage = app.dependency_overrides.get(get_storage, get_storage)()
    if isinstance(storage, MinioStorage):
        try:
            # Llamada bloqueante: se ejecuta en un hilo para no frenar el arranque del loop
            await run_in_threadpool(storage.ensure_bucket)
        except Exception:
            # La API debe arrancar aunque MinIO tarde; solo fallaran las subidas
            logger.exception("No se pudo preparar el bucket de MinIO")
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="BarazArte API",
        version="0.1.0",
        description="Galeria online de cuadros. La venta se gestiona solo por contacto.",
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        # PUT: lo usa PUT /admin/email-settings; sin él el navegador bloquea el preflight.
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request.state.request_id = f"req_{uuid.uuid4().hex[:12]}"
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    register_error_handlers(app)

    @app.get("/health", tags=["health"], summary="Estado del servicio")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    for router in (auth.router, public.router, panel.router, admin.router):
        app.include_router(router, prefix=API_PREFIX)
    return app


app = create_app()
