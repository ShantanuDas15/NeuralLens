"""Milestone 1.5 — Profile API Tests."""

from __future__ import annotations

import os
from unittest.mock import patch
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from main import app
from models.database import User, UserUsageStats

@pytest.fixture(scope="module", autouse=True)
def set_test_env():
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    yield

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"

@pytest.fixture(autouse=True)
async def setup_database():
    from db.session import AsyncSessionLocal, engine, init_db
    from models.database import Base

    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def mock_verify_token():
    with patch("middleware.auth.firebase_auth.verify_id_token") as mock:
        mock.return_value = {
            "uid": "test-uid-001",
            "email": "test@neurallens.com",
            "name": "Test User",
        }
        yield mock

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_profile_new_user(client, mock_verify_token):
    """Test 1 & 3: Valid token -> 200, stats all zeroes for new user."""
    response = client.get("/api/profile", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    data = response.json()
    assert data["uid"] == "test-uid-001"
    assert data["email"] == "test@neurallens.com"
    assert data["display_name"] == "Test User"
    assert data["auth_provider"] == "firebase"
    assert "member_since" in data
    
    stats = data["stats"]
    assert stats["total_jobs"] == 0
    assert stats["successful_jobs"] == 0
    assert stats["failed_jobs"] == 0
    assert stats["last_job_at"] is None

@pytest.mark.asyncio
async def test_profile_with_stats(client, mock_verify_token):
    """Test 2: stats.total_jobs reflects actual DB stats."""
    from db.session import AsyncSessionLocal
    
    # Init user
    client.get("/api/profile", headers={"Authorization": "Bearer fake-token"})
    
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.firebase_uid == "test-uid-001"))).scalar_one()
        stats = (await session.execute(select(UserUsageStats).where(UserUsageStats.user_id == user.id))).scalar_one()
        stats.total_jobs = 5
        stats.successful_jobs = 4
        stats.failed_jobs = 1
        stats.last_job_at = datetime.now(timezone.utc)
        await session.commit()
        
    response = client.get("/api/profile", headers={"Authorization": "Bearer fake-token"})
    assert response.status_code == 200
    data = response.json()
    
    stats_resp = data["stats"]
    assert stats_resp["total_jobs"] == 5
    assert stats_resp["successful_jobs"] == 4
    assert stats_resp["failed_jobs"] == 1
    assert stats_resp["last_job_at"] is not None

def test_profile_unauthenticated(client):
    """Test 4: Unauthenticated -> 422."""
    response = client.get("/api/profile")
    assert response.status_code == 422
