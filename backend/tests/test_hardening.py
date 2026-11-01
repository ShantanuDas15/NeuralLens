"""Tests for hardening behaviour: input limits, failure handling, cleanup."""

from __future__ import annotations

import io
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")
os.environ.setdefault("FIREBASE_SERVICE_ACCOUNT_PATH", "unused.json")

from main import app  # noqa: E402
from models.database import EnhancementJob, User, UserUsageStats  # noqa: E402

AUTH = {"Authorization": "Bearer fake-token"}


@pytest.fixture(autouse=True)
async def setup_database(tmp_path, monkeypatch):
    from routers.enhance import settings  # same object the router reads
    from db.session import engine, init_db
    from middleware.rate_limit import limiter
    from models.database import Base

    # These tests drop all tables on teardown: never run against a real DB.
    assert ":memory:" in str(engine.url), f"refusing to run on {engine.url}"
    limiter.reset()  # 5/min limit is shared across tests
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "results_dir", str(tmp_path / "results"))
    await init_db()
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    with patch("middleware.auth.firebase_auth.verify_id_token") as mock:
        mock.return_value = {"uid": "u-1", "email": "u1@example.com", "name": "U"}
        yield TestClient(app)


def _png(width: int, height: int) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height)).save(buf, format="PNG")
    return buf.getvalue()


def _post(client, data: bytes, name="a.png", scale=2):
    return client.post(
        "/api/enhance",
        headers=AUTH,
        files={"file": (name, data, "image/png")},
        data={"scale": str(scale)},
    )


def _ok_result(*_a, **_k):
    return b"png", {
        "input_width": 4, "input_height": 4,
        "output_width": 8, "output_height": 8, "processing_time_ms": 1,
    }


async def _jobs():
    from db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        return (await session.execute(select(EnhancementJob))).scalars().all()


def test_input_pixel_cap_returns_413(client, monkeypatch):
    from routers.enhance import settings  # same object the router reads

    monkeypatch.setattr(settings, "max_input_pixels", 100)
    assert _post(client, _png(20, 20)).status_code == 413


def test_output_pixel_cap_returns_413(client, monkeypatch):
    from routers.enhance import settings  # same object the router reads

    monkeypatch.setattr(settings, "max_output_pixels", 100)
    assert _post(client, _png(8, 8), scale=2).status_code == 413  # 64*4 > 100


def test_non_image_content_with_png_name_returns_415(client):
    assert _post(client, b"not an image at all", name="evil.png").status_code == 415


def test_gif_content_is_rejected(client):
    buf = io.BytesIO()
    Image.new("RGB", (4, 4)).save(buf, format="GIF")
    assert _post(client, buf.getvalue(), name="x.png").status_code == 415


@pytest.mark.asyncio
async def test_jpeg_upload_stored_as_jpeg(client):
    buf = io.BytesIO()
    Image.new("RGB", (4, 4)).save(buf, format="JPEG")
    with patch("routers.enhance.enhance_image", side_effect=_ok_result):
        resp = _post(client, buf.getvalue(), name="photo.jpg")
    assert resp.status_code == 200
    (job,) = await _jobs()
    assert job.input_format == "JPEG"
    assert job.input_file_path.endswith(".jpg")


@pytest.mark.asyncio
async def test_disk_write_failure_marks_job_failed(client):
    """A failure outside the inference call must still fail the job."""
    with patch("routers.enhance.enhance_image", side_effect=_ok_result), patch.object(
        Path, "write_bytes", side_effect=OSError("disk full")
    ):
        resp = _post(client, _png(4, 4))
    assert resp.status_code == 500
    (job,) = await _jobs()
    assert job.status == "failed"


@pytest.mark.asyncio
async def test_failed_job_removes_input_file(client, tmp_path):
    with patch("routers.enhance.enhance_image", side_effect=RuntimeError("boom")):
        resp = _post(client, _png(4, 4))
    assert resp.status_code == 500
    assert not list((tmp_path / "uploads").rglob("*.png"))


@pytest.mark.asyncio
async def test_oom_returns_503_and_fails_job(client):
    from services.srgan import InferenceOOMError

    with patch("routers.enhance.enhance_image", side_effect=InferenceOOMError("oom")):
        resp = _post(client, _png(4, 4))
    assert resp.status_code == 503
    (job,) = await _jobs()
    assert job.status == "failed"


@pytest.mark.asyncio
async def test_queue_timeout_returns_503(client, monkeypatch):
    import asyncio

    from routers.enhance import settings  # same object the router reads
    from routers import enhance

    monkeypatch.setattr(settings, "queue_timeout_seconds", 0.05)
    sem = asyncio.Semaphore(0)  # slot never frees up
    monkeypatch.setattr(enhance, "inference_semaphore", sem)
    resp = _post(client, _png(4, 4))
    assert resp.status_code == 503
    assert resp.headers.get("retry-after")
    (job,) = await _jobs()
    assert job.status == "failed"


@pytest.mark.asyncio
async def test_semaphore_released_after_failure(client):
    from routers import enhance

    with patch("routers.enhance.enhance_image", side_effect=RuntimeError("boom")):
        _post(client, _png(4, 4))
    assert not enhance.inference_semaphore.locked()


@pytest.mark.asyncio
async def test_missing_stats_row_does_not_break_failure_path(client):
    from db.session import AsyncSessionLocal

    with patch("routers.enhance.enhance_image", side_effect=_ok_result):
        _post(client, _png(4, 4))  # creates the user
    async with AsyncSessionLocal() as session:
        stats = (await session.execute(select(UserUsageStats))).scalar_one()
        await session.delete(stats)
        await session.commit()

    with patch("routers.enhance.enhance_image", side_effect=RuntimeError("boom")):
        assert _post(client, _png(4, 4)).status_code == 500
    async with AsyncSessionLocal() as session:
        stats = (await session.execute(select(UserUsageStats))).scalar_one()
        assert stats.failed_jobs == 1


@pytest.mark.asyncio
async def test_delete_history_removes_files(client):
    with patch("routers.enhance.enhance_image", side_effect=_ok_result):
        resp = _post(client, _png(4, 4))
    job_id = resp.json()["job_id"]
    (job,) = await _jobs()
    in_path, out_path = Path(job.input_file_path), Path(job.output_file_path)
    assert in_path.exists() and out_path.exists()

    assert client.delete(f"/api/history/{job_id}", headers=AUTH).status_code == 204
    assert not in_path.exists() and not out_path.exists()


def test_readiness_and_liveness_still_work(client):
    assert client.get("/health").status_code == 200


def test_queue_depth_cap_returns_503(client, monkeypatch):
    from routers import enhance

    monkeypatch.setattr(enhance.settings, "max_pending_jobs", 1)
    monkeypatch.setattr(enhance, "_in_flight", 1)  # one job already admitted
    resp = _post(client, _png(4, 4))
    assert resp.status_code == 503
    assert resp.headers.get("retry-after")


@pytest.mark.asyncio
async def test_rejected_by_queue_cap_creates_no_job(client, monkeypatch):
    from routers import enhance

    monkeypatch.setattr(enhance.settings, "max_pending_jobs", 1)
    monkeypatch.setattr(enhance, "_in_flight", 1)
    _post(client, _png(4, 4))
    assert await _jobs() == []


def test_in_flight_counter_released(client):
    from routers import enhance

    before = enhance._in_flight
    with patch("routers.enhance.enhance_image", side_effect=_ok_result):
        assert _post(client, _png(4, 4)).status_code == 200
    with patch("routers.enhance.enhance_image", side_effect=RuntimeError("boom")):
        assert _post(client, _png(4, 4)).status_code == 500
    assert enhance._in_flight == before


@pytest.mark.asyncio
async def test_fail_interrupted_jobs(client):
    from db.session import AsyncSessionLocal, fail_interrupted_jobs

    with patch("routers.enhance.enhance_image", side_effect=_ok_result):
        _post(client, _png(4, 4))  # one completed job
        _post(client, _png(4, 4))
    async with AsyncSessionLocal() as session:
        jobs = (await session.execute(select(EnhancementJob))).scalars().all()
        jobs[0].status = "processing"
        jobs[1].status = "pending"
        extra = jobs[1].id
        await session.commit()

    assert await fail_interrupted_jobs("restart") == 2
    assert await fail_interrupted_jobs("restart") == 0  # idempotent
    async with AsyncSessionLocal() as session:
        for job in (await session.execute(select(EnhancementJob))).scalars():
            assert job.status == "failed"
            assert job.error_message == "restart"
        assert extra
