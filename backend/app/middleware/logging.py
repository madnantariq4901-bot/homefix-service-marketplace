# app/middleware/logging.py
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware # pyright: ignore[reportMissingImports]
from starlette.requests import Request # pyright: ignore[reportMissingImports]

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("%s %s -> %s (%.1fms)", request.method, request.url.path, response.status_code, duration_ms)
        return response