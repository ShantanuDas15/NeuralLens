"""NeuralLens — async SQLAlchemy database session factory.

Provides:
    engine          — AsyncEngine connected to the configured DATABASE_URL
    AsyncSessionLocal — async_sessionmaker for creating AsyncSession instances
    get_db()        — FastAPI dependency that yields a scoped AsyncSession
    init_db()       — Creates all tables and seeds the model_configs table
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in str(type(dbapi_connection)).lower():
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _make_engine():
    """Create the async engine from the current settings.

    Import is deferred inside the function to allow tests to override
    DATABASE_URL in the environment before the engine is constructed.
    """
    from config import settings  # noqa: PLC0415

    connect_args = {}
    kwargs = {"echo": settings.debug, "future": True}

    if "sqlite" in settings.database_url:
        connect_args["check_same_thread"] = False
        if ":memory:" in settings.database_url:
            from sqlalchemy.pool import StaticPool

            kwargs["poolclass"] = StaticPool

    kwargs["connect_args"] = connect_args

    return create_async_engine(settings.database_url, **kwargs)


# Module-level engine — created once when this module is first imported.
engine = _make_engine()

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db():
    """FastAPI dependency: yield a database session, then close it.

    Usage in a router:
        db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables and seed the model_configs table.

    Safe to call multiple times (idempotent):
    - CREATE TABLE IF NOT EXISTS is used by SQLAlchemy's create_all().
    - Seed data is only inserted when the model_configs table is empty.
    """
    from sqlalchemy import select  # noqa: PLC0415

    from models.database import Base, ModelConfig  # noqa: PLC0415

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("All database tables created (or already exist).")

    # Seed the default Real-ESRGAN model config
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ModelConfig))
        existing = result.scalars().first()

        if existing is None:
            seed = ModelConfig(
                id=str(uuid.uuid4()),
                name="real-esrgan-x4plus",
                version="1.0.0",
                scale_factor=4,
                weights_filename="RealESRGAN_x4plus.pth",
                is_active=True,
                description=(
                    "Default 4× upscaling model. "
                    "General purpose photorealistic super-resolution."
                ),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(seed)
            await session.commit()
            logger.info("Seeded default model config: real-esrgan-x4plus")
        else:
            logger.info("model_configs already seeded — skipping.")
