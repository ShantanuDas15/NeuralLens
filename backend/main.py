"""NeuralLens — FastAPI application entry point.

Responsibilities:
- Application factory with async lifespan context manager
- CORS middleware registration
- Router registration for all API sub-modules
- Health check endpoint (unauthenticated)
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown hooks
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Run startup and shutdown logic around the application lifetime."""

    # ---- STARTUP -----------------------------------------------------------
    logger.info("NeuralLens backend starting up…")

    # 1. Ensure storage directories exist
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.results_dir, exist_ok=True)
    logger.info(
        "Storage directories ready: %s, %s", settings.upload_dir, settings.results_dir
    )

    # 2. Initialise database (create tables + seed model_configs)
    #    Import deferred here to avoid circular imports at module load time.
    from db.session import init_db  # noqa: PLC0415

    await init_db()
    logger.info("Database initialised.")

    # 3. Initialise Firebase Admin SDK
    #    Wrapped in try/except so the server still starts if the service
    #    account file is missing (useful for running unit tests without creds).
    try:
        import firebase_admin  # noqa: PLC0415
        from firebase_admin import credentials  # noqa: PLC0415

        if not firebase_admin._apps:  # avoid re-initialising in tests
            cred = credentials.Certificate(settings.firebase_service_account_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialised.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Firebase Admin SDK not initialised: %s", exc)

    # 4. Load SRGAN model singleton
    #    Also deferred — skipped gracefully if weights are absent.
    try:
        from services.srgan import load_model  # noqa: PLC0415

        load_model()
        logger.info("SRGAN model loaded.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("SRGAN model could not be loaded at startup: %s", exc)

    yield  # ---- Application runs here ----

    # ---- SHUTDOWN ----------------------------------------------------------
    logger.info("NeuralLens backend shutting down.")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    """Construct and configure the FastAPI application instance."""

    application = FastAPI(
        title="NeuralLens API",
        description="AI-Powered Image Super-Resolution — Backend API",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers (registered once the modules exist — stubs registered now)
    # Each router is imported lazily so that missing optional deps don't
    # crash the import at startup during early development stages.
    _register_routers(application)

    return application


def _register_routers(application: FastAPI) -> None:
    """Register all API routers onto the application."""

    try:
        from routers import enhance, history, profile  # noqa: PLC0415

        application.include_router(enhance.router, prefix="/api", tags=["enhance"])
        application.include_router(history.router, prefix="/api", tags=["history"])
        application.include_router(profile.router, prefix="/api", tags=["profile"])
        logger.info("All API routers registered.")
    except ImportError as exc:
        logger.warning(
            "Some routers could not be imported (expected during scaffold): %s", exc
        )


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------
app: FastAPI = create_app()


# ---------------------------------------------------------------------------
# Health check — unauthenticated, always available
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"], summary="Liveness check")
async def health_check() -> dict[str, str]:
    """Return a simple liveness confirmation.

    Used by load balancers, uptime monitors, and CI smoke tests.
    No authentication required.
    """
    return {"status": "ok", "version": settings.app_version}
