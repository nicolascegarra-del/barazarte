"""Rate limiting por IP con ventana fija (Redis en produccion, memoria en tests)."""

import logging
import threading
import time
from collections.abc import Callable
from functools import lru_cache
from typing import Protocol

import redis
from fastapi import Request

from app.core.config import get_settings
from app.core.errors import AppError

logger = logging.getLogger(__name__)


class RateLimiter(Protocol):
    def hit(self, key: str, limit: int, window_seconds: int) -> bool:
        """Registra una peticion. Devuelve False si se supera el limite."""
        ...


class MemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, tuple[int, float]] = {}
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        with self._lock:
            count, expires_at = self._hits.get(key, (0, 0.0))
            if now >= expires_at:
                count, expires_at = 0, now + window_seconds
            count += 1
            self._hits[key] = (count, expires_at)
            return count <= limit


class RedisRateLimiter:
    def __init__(self, url: str) -> None:
        self._client = redis.Redis.from_url(url)

    def hit(self, key: str, limit: int, window_seconds: int) -> bool:
        try:
            redis_key = f"ratelimit:{key}"
            count = int(self._client.incr(redis_key))
            if count == 1:
                self._client.expire(redis_key, window_seconds)
            return count <= limit
        except redis.RedisError:
            # Fail-open: una caida de Redis no debe tumbar el login ni el formulario,
            # pero queda registrado para alertar.
            logger.exception("Redis no disponible; rate limit omitido")
            return True


@lru_cache
def get_rate_limiter() -> RateLimiter:
    settings = get_settings()
    if settings.rate_limit_backend == "memory":
        return MemoryRateLimiter()
    return RedisRateLimiter(settings.redis_url)


def client_ip(request: Request) -> str:
    if get_settings().trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(
    scope: str, limit_getter: Callable[[], tuple[int, int]]
) -> Callable[[Request], None]:
    """Crea una dependencia FastAPI. `limit_getter` devuelve (limite, ventana_segundos)
    y se evalua en cada peticion para respetar la configuracion actual."""

    def dependency(request: Request) -> None:
        limit, window = limit_getter()
        if not get_rate_limiter().hit(f"{scope}:{client_ip(request)}", limit, window):
            raise AppError(
                429,
                "RATE_LIMITED",
                "Demasiadas peticiones. Espera un momento e intentalo de nuevo.",
                headers={"Retry-After": str(window)},
            )

    return dependency
