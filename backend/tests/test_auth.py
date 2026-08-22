"""Milestone 1.3 — Firebase Auth Middleware Tests.

Verify token decoding, user database upserts, error handling,
and audit logging — without making live Firebase API calls.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from firebase_admin.auth import InvalidIdTokenError, RevokedIdTokenError
from sqlalchemy import select

# We use the real database fixture setup from Milestone 1.2
from middleware.auth import get_current_user
from models.database import AuditLog, User, UserUsageStats

# ---------------------------------------------------------------------------
# Test App Setup
# ---------------------------------------------------------------------------

# We create a dummy app here instead of importing main.py so we can test
# the dependency in isolation without pulling in all routers.
test_app = FastAPI()


@test_app.get("/protected")
async def protected_route(user: User = Depends(get_current_user)):
    return {"firebase_uid": user.firebase_uid, "email": user.email}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def set_test_env():
    """Set in-memory DB for tests."""
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    yield


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def setup_database():
    """Ensure database is initialized and tables created before each test."""
    from db.session import AsyncSessionLocal, engine, init_db
    from models.database import Base

    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_verify_token():
    """Mock firebase_admin.auth.verify_id_token to return a fake payload."""
    with patch("middleware.auth.firebase_auth.verify_id_token") as mock:
        mock.return_value = {
            "uid": "test-uid-001",
            "email": "test@neurallens.com",
            "name": "Test User",
        }
        yield mock


@pytest.fixture
def client():
    """TestClient for the dummy test app."""
    return TestClient(test_app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_valid_token_returns_user(client, mock_verify_token):
    """Test 1: Valid mock token → returns User object with correct firebase_uid."""
    response = client.get("/protected", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    assert response.json() == {
        "firebase_uid": "test-uid-001",
        "email": "test@neurallens.com",
    }
    mock_verify_token.assert_called_once_with("fake-token", check_revoked=True)


@pytest.mark.asyncio
async def test_valid_token_upserts_user_and_stats(client, mock_verify_token):
    """Test 2: Valid token → user and user_usage_stats rows upserted in DB."""
    from db.session import AsyncSessionLocal

    # Trigger the request
    client.get("/protected", headers={"Authorization": "Bearer fake-token"})

    # Check DB
    async with AsyncSessionLocal() as session:
        # Check User
        res = await session.execute(
            select(User).where(User.firebase_uid == "test-uid-001")
        )
        user = res.scalar_one_or_none()
        assert user is not None
        assert user.email == "test@neurallens.com"

        # Check Stats
        res_stats = await session.execute(
            select(UserUsageStats).where(UserUsageStats.user_id == user.id)
        )
        stats = res_stats.scalar_one_or_none()
        assert stats is not None
        assert stats.total_jobs == 0


@pytest.mark.asyncio
async def test_valid_token_idempotent_upsert(client, mock_verify_token):
    """Test 3: Valid token second call → no duplicate user row (upsert idempotent)."""
    from db.session import AsyncSessionLocal

    # First call
    client.get("/protected", headers={"Authorization": "Bearer fake-token"})

    # Change mock slightly to test update behavior
    mock_verify_token.return_value["name"] = "Updated Name"

    # Second call
    client.get("/protected", headers={"Authorization": "Bearer fake-token"})

    async with AsyncSessionLocal() as session:
        # Verify exactly one user exists with this UID
        res = await session.execute(
            select(User).where(User.firebase_uid == "test-uid-001")
        )
        users = res.scalars().all()
        assert len(users) == 1
        assert users[0].display_name == "Updated Name"

        # Verify exactly one stats row exists
        res_stats = await session.execute(
            select(UserUsageStats).where(UserUsageStats.user_id == users[0].id)
        )
        stats = res_stats.scalars().all()
        assert len(stats) == 1


def test_missing_auth_header(client):
    """Test 4: Missing Authorization header → HTTP 422 (Unprocessable Entity)."""
    # FastAPI's Header(...) dependency will automatically raise a 422 if the header is missing
    response = client.get("/protected")
    assert response.status_code == 422


def test_malformed_bearer_prefix(client):
    """Test 5: Malformed "Bearer" prefix → HTTP 401."""
    response = client.get("/protected", headers={"Authorization": "Token fake-token"})
    assert response.status_code == 401
    assert "Bearer" in response.json()["detail"]


def test_expired_token(client, mock_verify_token):
    """Test 6: Expired/invalid token → HTTP 401."""
    mock_verify_token.side_effect = InvalidIdTokenError("Token expired")
    response = client.get("/protected", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


def test_revoked_token(client, mock_verify_token):
    """Test 7: Revoked token → HTTP 401."""
    mock_verify_token.side_effect = RevokedIdTokenError("Token revoked")
    response = client.get("/protected", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_audit_logs_written_on_success(client, mock_verify_token):
    """Test 8: audit_logs row with action="user.login" written on successful auth."""
    from db.session import AsyncSessionLocal

    client.get("/protected", headers={"Authorization": "Bearer fake-token"})

    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(AuditLog).where(AuditLog.action == "user.login")
        )
        logs = res.scalars().all()
        assert len(logs) == 1

        # Check it maps to our user
        user_res = await session.execute(
            select(User).where(User.firebase_uid == "test-uid-001")
        )
        user = user_res.scalar_one()
        assert logs[0].user_id == user.id
