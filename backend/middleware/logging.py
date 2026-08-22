"""Structured logging middleware."""

import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


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

        response = await call_next(request)

        # We can add a custom header to the response to trace it back
        response.headers["X-Request-ID"] = req_id
        return response
