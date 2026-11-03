"""Request-size limiting and security headers (pure ASGI middleware).

FastAPI parses a multipart body *before* running dependencies, so the handler's
own size check cannot protect against an oversized (or unauthenticated) upload:
the whole body has already been received and spooled by then. The limiter here
rejects such requests up front, both from the declared Content-Length and while
streaming, which also covers chunked bodies that declare no length at all.
"""

from __future__ import annotations

import re

from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Multipart framing (boundaries, part headers, the scale field) on top of the file.
MULTIPART_OVERHEAD = 64 * 1024

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class _BodyTooLarge(Exception):
    pass


class BodySizeLimitMiddleware:
    """Reject HTTP requests whose body exceeds ``max_bytes`` with a 413."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None and declared.isdigit() and int(declared) > self.max_bytes:
            await self._reject(send)
            return

        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _BodyTooLarge
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracking_send)
        except _BodyTooLarge:
            if not response_started:
                await self._reject(send)

    @staticmethod
    async def _reject(send: Send) -> None:
        body = b'{"detail":"Request body too large"}'
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                    (b"connection", b"close"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


class SecurityHeadersMiddleware:
    """Add baseline security headers to every HTTP response."""

    def __init__(self, app: ASGIApp, *, strict_csp: bool = True) -> None:
        self.app = app
        headers = [
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
            (b"referrer-policy", b"no-referrer"),
            (b"strict-transport-security", b"max-age=31536000; includeSubDomains"),
        ]
        if strict_csp:
            # The API serves JSON and images only; nothing here should render.
            headers.append(
                (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'")
            )
        self._headers = headers

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                present = {name.lower() for name, _ in message["headers"]}
                message["headers"] = list(message["headers"]) + [
                    h for h in self._headers if h[0] not in present
                ]
            await send(message)

        await self.app(scope, receive, send_with_headers)


def sanitize_request_id(value: str | None, fallback: str) -> str:
    """Accept a client-supplied request ID only if it is short and log-safe."""
    if value and _REQUEST_ID_RE.match(value):
        return value
    return fallback
