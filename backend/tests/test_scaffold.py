"""Milestone 1.1 — Scaffold & Environment Verification Tests.

Tests verify:
1. config.py loads Settings with correct defaults
2. Settings.max_upload_bytes default is exactly 2 MB
3. Settings.app_version default is "1.0.0"
4. FastAPI app object is created and is a FastAPI instance
5. GET /health returns HTTP 200
6. GET /health response body is {"status": "ok", "version": "1.0.0"}
7. GET /health does NOT require authentication
8. Swagger docs endpoint (/docs) is accessible (returns 200)
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def set_test_env(tmp_path_factory):
    """Inject minimal environment variables so Settings can be instantiated
    without a real .env file during CI / test runs."""
    tmp = tmp_path_factory.mktemp("data")
    env_vars = {
        "FIREBASE_PROJECT_ID": "test-project",
        "FIREBASE_SERVICE_ACCOUNT_PATH": str(tmp / "fake-sa.json"),
        "DATABASE_URL": "sqlite+aiosqlite:///./neurallens_test.db",
        "UPLOAD_DIR": str(tmp / "uploads"),
        "RESULTS_DIR": str(tmp / "results"),
        "DEBUG": "false",
    }
    for key, value in env_vars.items():
        os.environ.setdefault(key, value)
    yield
    # Cleanup: remove the test DB file if it was created
    test_db = "./neurallens_test.db"
    if os.path.exists(test_db):
        os.remove(test_db)


@pytest.fixture(scope="module")
def test_client():
    """Return a synchronous TestClient wrapping the FastAPI app.

    The lifespan is intentionally NOT triggered here — we test the app
    object and routing in isolation without requiring Firebase or DB.
    """
    # We must import *after* env vars are set to avoid Settings validation error
    from main import app  # noqa: PLC0415

    with TestClient(app, raise_server_exceptions=True) as client:
        yield client


# ---------------------------------------------------------------------------
# Test 1: Settings defaults
# ---------------------------------------------------------------------------


def test_settings_loads():
    """Settings can be instantiated from environment variables."""
    from config import Settings  # noqa: PLC0415

    s = Settings()
    assert s is not None


def test_settings_max_upload_bytes_default():
    """Default max_upload_bytes is 2 MB (2,097,152 bytes)."""
    from config import Settings  # noqa: PLC0415

    s = Settings()
    assert s.max_upload_bytes == 2_097_152


def test_settings_app_version_default():
    """Default app_version is '1.0.0'."""
    from config import Settings  # noqa: PLC0415

    s = Settings()
    assert s.app_version == "1.0.0"


def test_settings_database_url_uses_sqlite():
    """Default database URL targets SQLite."""
    from config import Settings  # noqa: PLC0415

    s = Settings()
    assert "sqlite" in s.database_url


# ---------------------------------------------------------------------------
# Test 2: App object
# ---------------------------------------------------------------------------


def test_app_is_fastapi_instance():
    """main.app is a FastAPI application instance."""
    from fastapi import FastAPI  # noqa: PLC0415

    from main import app  # noqa: PLC0415

    assert isinstance(app, FastAPI)


def test_app_title():
    """App title is correctly set."""
    from main import app  # noqa: PLC0415

    assert app.title == "NeuralLens API"


# ---------------------------------------------------------------------------
# Test 3: Health endpoint
# ---------------------------------------------------------------------------


def test_health_returns_200(test_client):
    """GET /health returns HTTP 200."""
    response = test_client.get("/health")
    assert response.status_code == 200


def test_health_response_body(test_client):
    """GET /health response body contains status=ok and version."""
    response = test_client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert body["version"] == "1.0.0"


def test_health_no_auth_required(test_client):
    """GET /health succeeds without any Authorization header."""
    response = test_client.get("/health")
    # Must NOT return 401 or 403
    assert response.status_code not in (401, 403)


# ---------------------------------------------------------------------------
# Test 4: Docs endpoint
# ---------------------------------------------------------------------------


def test_docs_accessible(test_client):
    """Swagger UI (/docs) returns HTTP 200."""
    response = test_client.get("/docs")
    assert response.status_code == 200
