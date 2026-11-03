"""Tests for production hardening: body limit, headers, rate limit, auth races."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import func, select
from starlette.requests import Request

from middleware.limits import (
    BodySizeLimitMiddleware,
    SecurityHeadersMiddleware,
    sanitize_request_id,
)
from middleware.rate_limit import build_limiter
from models.database import AuditLog, User, UserUsageStats


# ---------------------------------------------------------------------------
# Body size limit
# ---------------------------------------------------------------------------


def _echo_app_raw(max_bytes: int) -> FastAPI:
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=max_bytes)

    @app.post("/echo")
    async def echo(request: Request):
        return {"size": len(await request.body())}

    return app


def test_body_within_limit_passes():
    client = TestClient(_echo_app_raw(100))
    assert client.post("/echo", content=b"x" * 100).json() == {"size": 100}


def test_declared_oversize_body_rejected_before_reading():
    client = TestClient(_echo_app_raw(100))
    response = client.post("/echo", content=b"x" * 101)
    assert response.status_code == 413
    assert response.json() == {"detail": "Request body too large"}


def test_chunked_oversize_body_rejected_while_streaming():
    """No Content-Length: the limit must still hold as the body streams in."""

    def chunks():
        for _ in range(5):
            yield b"x" * 40

    client = TestClient(_echo_app_raw(100))
    response = client.post("/echo", content=chunks())
    assert response.status_code == 413


def test_real_app_rejects_oversized_upload_without_auth():
    """The unauthenticated-large-upload case from the audit (F-06)."""
    from main import app
    from config import settings

    big = b"x" * (settings.max_upload_bytes + 200_000)
    response = TestClient(app).post(
        "/api/enhance", files={"file": ("a.png", big, "image/png")}
    )
    assert response.status_code == 413


# ---------------------------------------------------------------------------
# Security headers and request IDs
# ---------------------------------------------------------------------------


def test_security_headers_present_on_real_app():
    from main import app

    headers = TestClient(app).get("/health").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert "max-age" in headers["strict-transport-security"]
    assert "default-src 'none'" in headers["content-security-policy"]


def test_csp_can_be_disabled_for_debug_docs():
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware, strict_csp=False)

    @app.get("/")
    async def root():
        return {}

    headers = TestClient(app).get("/").headers
    assert "content-security-policy" not in headers
    assert headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize(
    "value,expected",
    [
        ("abc-123_DEF.9", "abc-123_DEF.9"),
        ("a" * 64, "a" * 64),
        ("a" * 65, "fallback"),
        ("bad id", "fallback"),
        ('x"\\n{"forged":1}', "fallback"),
        ("", "fallback"),
        (None, "fallback"),
    ],
)
def test_sanitize_request_id(value, expected):
    assert sanitize_request_id(value, "fallback") == expected


def test_unsafe_request_id_is_replaced_in_response():
    from main import app

    response = TestClient(app).get("/health", headers={"X-Request-ID": "bad id!"})
    assert response.headers["x-request-id"] != "bad id!"


# ---------------------------------------------------------------------------
# Default rate limit
# ---------------------------------------------------------------------------


def test_default_rate_limit_applies_to_every_route():
    limiter = build_limiter("2/minute")
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.get("/thing")
    async def thing(request: Request):
        return {}

    @app.get("/health")
    @limiter.exempt
    async def health():
        return {}

    client = TestClient(app)
    assert [client.get("/thing").status_code for _ in range(3)] == [200, 200, 429]
    assert all(client.get("/health").status_code == 200 for _ in range(5))


def test_empty_default_means_no_default_limit():
    assert build_limiter("")._default_limits == []


# ---------------------------------------------------------------------------
# Auth: login auditing and first-login race
# ---------------------------------------------------------------------------

TOKEN = {"uid": "race-uid", "email": "race@example.com", "name": "Race"}
HEADERS = {"Authorization": "Bearer fake-token"}


@pytest.fixture
async def db_ready():
    from db.session import engine, init_db
    from models.database import Base

    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def auth_client():
    from fastapi import Depends

    from middleware.auth import get_current_user

    app = FastAPI()

    @app.get("/me")
    async def me(user: User = Depends(get_current_user)):
        return {"uid": user.firebase_uid}

    with patch("middleware.auth.firebase_auth.verify_id_token") as mock:
        mock.return_value = dict(TOKEN)
        yield TestClient(app), mock


async def _count(model):
    from db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        return (await session.execute(select(func.count()).select_from(model))).scalar_one()


async def test_repeated_requests_write_one_audit_row(db_ready, auth_client):
    client, _ = auth_client
    for _ in range(5):
        assert client.get("/me", headers=HEADERS).status_code == 200
    assert await _count(AuditLog) == 1
    assert await _count(UserUsageStats) == 1


async def test_login_recorded_again_after_quiet_period(db_ready, auth_client):
    from db.session import AsyncSessionLocal

    client, _ = auth_client
    client.get("/me", headers=HEADERS)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User))).scalar_one()
        user.last_login_at = datetime.now(timezone.utc) - timedelta(hours=2)
        await session.commit()

    client.get("/me", headers=HEADERS)
    assert await _count(AuditLog) == 2


async def test_first_login_race_recovers_instead_of_500(db_ready, auth_client):
    """Simulate losing the insert race: the row appears just before our flush."""
    from db.session import AsyncSessionLocal
    from sqlalchemy.ext.asyncio import AsyncSession

    client, _ = auth_client
    real_flush = AsyncSession.flush
    state = {"raced": False}

    async def racing_flush(self, *a, **k):
        if not state["raced"] and any(isinstance(o, User) for o in self.new):
            state["raced"] = True
            async with AsyncSessionLocal() as other:  # the "winning" request
                other.add(User(firebase_uid="race-uid", email="race@example.com"))
                await other.commit()
        return await real_flush(self, *a, **k)

    with patch.object(AsyncSession, "flush", racing_flush):
        response = client.get("/me", headers=HEADERS)

    assert state["raced"]
    assert response.status_code == 200
    assert await _count(User) == 1


async def test_email_owned_by_other_account_returns_409(db_ready, auth_client):
    from db.session import AsyncSessionLocal

    client, mock = auth_client
    async with AsyncSessionLocal() as session:
        session.add(User(firebase_uid="someone-else", email="race@example.com"))
        await session.commit()

    response = client.get("/me", headers=HEADERS)
    assert response.status_code == 409
    assert await _count(User) == 1
