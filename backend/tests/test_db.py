"""Milestone 1.2 — Database Layer Tests.

Tests verify:
1. init_db() creates all 5 tables without error (in-memory SQLite)
2. ModelConfig seed row is inserted exactly once (idempotent)
3. User row can be inserted, retrieved by firebase_uid, and soft-deleted
4. EnhancementJob FK constraint enforced — job without valid user_id raises IntegrityError
5. UserUsageStats unique constraint on user_id — second insert raises IntegrityError
6. AuditLog row inserted and created_at is immutable (no updated_at column)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def set_test_env():
    """Set in-memory DB for tests."""
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    # Also set dummy values for config
    os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")
    os.environ.setdefault("FIREBASE_SERVICE_ACCOUNT_PATH", "fake.json")
    yield


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def setup_database():
    """Ensure database is initialized and tables created before each test."""
    from db.session import AsyncSessionLocal, engine, init_db
    from models.database import Base

    # Create tables and seed data
    await init_db()
    yield
    # Teardown: drop tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_init_db_creates_all_tables():
    """init_db() creates all 5 tables without error."""
    from db.session import engine

    def get_table_names(connection):
        inspector = inspect(connection)
        return inspector.get_table_names()

    async with engine.connect() as conn:
        tables = await conn.run_sync(get_table_names)

    expected_tables = {
        "users",
        "model_configs",
        "enhancement_jobs",
        "user_usage_stats",
        "audit_logs",
    }
    assert expected_tables.issubset(set(tables))


@pytest.mark.asyncio
async def test_model_config_seed_idempotent():
    """ModelConfig seed row is inserted exactly once, even if init_db is called twice."""
    from db.session import AsyncSessionLocal, init_db
    from models.database import ModelConfig

    # Call init_db a second time
    await init_db()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ModelConfig).where(ModelConfig.name == "real-esrgan-x4plus")
        )
        configs = result.scalars().all()

    # Ensure there is exactly one row
    assert len(configs) == 1
    assert configs[0].scale_factor == 4


@pytest.mark.asyncio
async def test_user_crud():
    """User row can be inserted, retrieved by firebase_uid, and soft-deleted."""
    from db.session import AsyncSessionLocal
    from models.database import User

    # 1. Insert
    async with AsyncSessionLocal() as session:
        user = User(
            firebase_uid="test-uid-123",
            email="test@example.com",
            display_name="Test User",
        )
        session.add(user)
        await session.commit()

    # 2. Retrieve
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.firebase_uid == "test-uid-123")
        )
        db_user = result.scalar_one_or_none()
        assert db_user is not None
        assert db_user.email == "test@example.com"
        assert db_user.deleted_at is None

    # 3. Soft Delete
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.firebase_uid == "test-uid-123")
        )
        db_user = result.scalar_one_or_none()
        db_user.deleted_at = datetime.now(timezone.utc)
        await session.commit()

    # Verify soft delete
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.firebase_uid == "test-uid-123")
        )
        db_user = result.scalar_one_or_none()
        assert db_user.deleted_at is not None


@pytest.mark.asyncio
async def test_enhancement_job_fk_constraint():
    """EnhancementJob without valid user_id raises IntegrityError."""
    from db.session import AsyncSessionLocal
    from models.database import EnhancementJob, ModelConfig

    async with AsyncSessionLocal() as session:
        # Get the seeded model_config
        result = await session.execute(select(ModelConfig))
        model_config = result.scalars().first()

        job = EnhancementJob(
            user_id="invalid-user-id",  # Fake FK
            model_config_id=model_config.id,
            original_filename="test.png",
            input_file_path="uploads/test/test.png",
            input_size_bytes=1000,
            input_width=64,
            input_height=64,
            input_format="png",
        )
        session.add(job)
        with pytest.raises(IntegrityError):
            await session.commit()


@pytest.mark.asyncio
async def test_user_usage_stats_unique_constraint():
    """UserUsageStats unique constraint on user_id — second insert raises IntegrityError."""
    from db.session import AsyncSessionLocal
    from models.database import User, UserUsageStats

    async with AsyncSessionLocal() as session:
        # Create user
        user = User(firebase_uid="uid-stats", email="stats@example.com")
        session.add(user)
        await session.commit()

        # Add first stats row
        stats1 = UserUsageStats(user_id=user.id)
        session.add(stats1)
        await session.commit()

        # Add second stats row for same user
        stats2 = UserUsageStats(user_id=user.id)
        session.add(stats2)
        with pytest.raises(IntegrityError):
            await session.commit()


@pytest.mark.asyncio
async def test_audit_log_immutable():
    """AuditLog row inserted and created_at is immutable (no updated_at column)."""
    from db.session import AsyncSessionLocal
    from models.database import AuditLog, User

    async with AsyncSessionLocal() as session:
        # Create user
        user = User(firebase_uid="uid-audit", email="audit@example.com")
        session.add(user)
        await session.commit()

        # Create log
        log = AuditLog(
            user_id=user.id,
            action="user.login",
            ip_address="127.0.0.1",
        )
        session.add(log)
        await session.commit()

        # Verify
        result = await session.execute(
            select(AuditLog).where(AuditLog.user_id == user.id)
        )
        db_log = result.scalar_one_or_none()
        assert db_log is not None
        assert db_log.action == "user.login"
        assert hasattr(db_log, "created_at")
        assert not hasattr(db_log, "updated_at")
