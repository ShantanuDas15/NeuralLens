"""Milestone 1.5 — Enhance API Tests.

Tests the POST /api/enhance endpoint.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from main import app
from models.database import EnhancementJob, User, UserUsageStats

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def set_test_env():
    """Set in-memory DB for tests and override settings."""
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    # Use small limits for testing
    os.environ["MAX_UPLOAD_BYTES"] = "2097152"  # 2MB

    # Reload config to apply
    import importlib

    import config

    importlib.reload(config)
    yield


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def setup_database():
    """Ensure database is initialized before each test."""
    from db.session import AsyncSessionLocal, engine, init_db
    from models.database import Base

    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_verify_token():
    """Mock firebase token verification."""
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


@pytest.fixture
def mock_enhance_image():
    """Mock the actual SRGAN inference to return dummy bytes."""
    with patch("routers.enhance.enhance_image") as mock:
        # returns (result_bytes, metadata)
        mock.return_value = (
            b"fake_png_data",
            {
                "input_width": 128,
                "input_height": 128,
                "output_width": 512,
                "output_height": 512,
                "processing_time_ms": 450,
            },
        )
        yield mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enhance_unauthenticated(client):
    """Test 5: Unauthenticated request (no Bearer header) -> 401."""
    response = client.post(
        "/api/enhance", files={"file": ("test.png", b"fake", "image/png")}
    )
    assert (
        response.status_code == 422
    )  # Because of missing Authorization header (422 by FastAPI Header validation)


def test_malformed_auth(client):
    response = client.post(
        "/api/enhance",
        headers={"Authorization": "Bearer fake-token"},
        # No file
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_enhance_no_file(client, mock_verify_token):
    """Test 2: No file attached -> 422."""
    response = client.post(
        "/api/enhance", headers={"Authorization": "Bearer fake-token"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_enhance_file_too_large(client, mock_verify_token):
    """Test 3: File exceeds 2MB -> 413."""
    big_file = b"0" * (2 * 1024 * 1024 + 1)
    response = client.post(
        "/api/enhance",
        headers={"Authorization": "Bearer fake-token"},
        files={"file": ("big.png", big_file, "image/png")},
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_enhance_unsupported_format(client, mock_verify_token):
    """Test 4: Non-image file (text/plain) -> 415."""
    response = client.post(
        "/api/enhance",
        headers={"Authorization": "Bearer fake-token"},
        files={"file": ("test.txt", b"text", "text/plain")},
    )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_enhance_valid_upload(client, mock_verify_token, mock_enhance_image):
    """Test 1, 6, 7: Valid upload -> 200, job status completed, stats updated."""
    client.get("/api/profile", headers={"Authorization": "Bearer fake-token"})

    # 1x1 black PNG
    import base64

    valid_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
    )

    response = client.post(
        "/api/enhance",
        headers={"Authorization": "Bearer fake-token"},
        files={"file": ("test.png", valid_png, "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "completed"
    assert data["result_url"].startswith("/api/results/")
    assert data["output_w"] == 512

    # Check DB state
    from db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        # Check job
        job_res = await session.execute(
            select(EnhancementJob).where(EnhancementJob.id == data["job_id"])
        )
        job = job_res.scalar_one()
        assert job.status == "completed"

        # Check stats
        stats_res = await session.execute(
            select(UserUsageStats).where(UserUsageStats.user_id == job.user_id)
        )
        stats = stats_res.scalar_one()
        assert stats.successful_jobs == 1
        assert stats.total_jobs == 1


@pytest.mark.asyncio
async def test_enhance_inference_error(client, mock_verify_token, mock_enhance_image):
    """Test 8: SRGAN mock raises RuntimeError -> job status = "failed", response 500."""
    client.get("/api/profile", headers={"Authorization": "Bearer fake-token"})

    mock_enhance_image.side_effect = RuntimeError("GPU out of memory")

    import base64

    valid_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAACklEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
    )

    response = client.post(
        "/api/enhance",
        headers={"Authorization": "Bearer fake-token"},
        files={"file": ("test.png", valid_png, "image/png")},
    )

    assert response.status_code == 500
    assert "error" in response.json()["detail"].lower()

    # Check DB state for failed job
    from db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        # Find the user
        user_res = await session.execute(
            select(User).where(User.firebase_uid == "test-uid-001")
        )
        user = user_res.scalar_one()

        # Check job
        job_res = await session.execute(
            select(EnhancementJob).where(EnhancementJob.user_id == user.id)
        )
        job = job_res.scalars().first()
        assert job.status == "failed"
        assert job.error_message == "GPU out of memory"

        # Check stats
        stats_res = await session.execute(
            select(UserUsageStats).where(UserUsageStats.user_id == user.id)
        )
        stats = stats_res.scalar_one()
        assert stats.failed_jobs == 1
        assert stats.successful_jobs == 0
