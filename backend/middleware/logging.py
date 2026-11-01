"""Structured request logging middleware."""

import time
import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

log = structlog.get_logger("access")


class StructlogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=req_id,
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None,
        )

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            log.error(
                "request failed",
                duration_ms=int((time.perf_counter() - start) * 1000),
                exc_info=True,
            )
            raise

        log.info(
            "request completed",
            status=response.status_code,
            duration_ms=int((time.perf_counter() - start) * 1000),
        )
        response.headers["X-Request-ID"] = req_id
        structlog.contextvars.clear_contextvars()
        return response
