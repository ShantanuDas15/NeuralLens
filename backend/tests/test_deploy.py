"""Tests for deployment-readiness behaviour: URL normalisation, /ready, migrations."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parent.parent

os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")


@pytest.mark.parametrize(
    "raw",
    [
        "postgres://u:p@h:5432/d",
        "postgresql://u:p@h:5432/d",
        "postgresql+asyncpg://u:p@h:5432/d",
    ],
)
def test_postgres_urls_use_asyncpg(raw):
    from config import Settings

    s = Settings(firebase_project_id="x", database_url=raw)
    assert s.database_url == "postgresql+asyncpg://u:p@h:5432/d"


def test_sqlite_url_untouched():
    from config import Settings

    url = "sqlite+aiosqlite:///./x.db"
    assert Settings(firebase_project_id="x", database_url=url).database_url == url


def test_ready_503_when_model_missing(monkeypatch):
    import services.srgan as srgan
    from main import app

    with TestClient(app) as client:  # startup may load real weights
        monkeypatch.setattr(srgan, "_model_instances", {})
        resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json()["checks"]["model"] is False


def test_ready_200_when_model_loaded(monkeypatch):
    import services.srgan as srgan
    from main import app

    import firebase_admin

    with TestClient(app) as client:
        monkeypatch.setattr(srgan, "_model_instances", {4: object()})
        monkeypatch.setattr(firebase_admin, "_apps", {"[DEFAULT]": object()})
        resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


def test_ready_503_when_firebase_not_initialised(monkeypatch):
    import firebase_admin

    import services.srgan as srgan
    from main import app

    with TestClient(app) as client:
        monkeypatch.setattr(srgan, "_model_instances", {4: object()})
        monkeypatch.setattr(firebase_admin, "_apps", {})
        resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json()["checks"]["firebase"] is False


def test_require_firebase_fails_startup(monkeypatch):
    import firebase_admin

    from config import settings
    from main import app

    monkeypatch.setattr(settings, "require_firebase", True)
    monkeypatch.setattr(firebase_admin, "_apps", {})
    with pytest.raises(RuntimeError, match="REQUIRE_FIREBASE"):
        with TestClient(app):
            pass


def test_alembic_upgrade_and_downgrade(tmp_path):
    """The migration chain creates the schema and can be reverted."""
    env = {
        **os.environ,
        "FIREBASE_PROJECT_ID": "test-project",
        "DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path / 'mig.db'}",
    }
    for cmd in (["upgrade", "head"], ["downgrade", "base"]):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *cmd],
            cwd=BACKEND, env=env, capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
