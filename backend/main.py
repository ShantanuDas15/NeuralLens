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

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import settings
from middleware.limits import (
    MULTIPART_OVERHEAD,
    BodySizeLimitMiddleware,
    SecurityHeadersMiddleware,
)
from middleware.rate_limit import limiter

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# structlog renders to stdlib handlers; without a configured root logger the
# INFO records from stdlib-logging modules (srgan, enhance, auth) are dropped.
logging.basicConfig(format="%(message)s", level=logging.INFO)

# Replace the default logger with structlog
logger = structlog.get_logger(__name__)


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

    from db.session import fail_interrupted_jobs  # noqa: PLC0415

    stale = await fail_interrupted_jobs("Interrupted by a server restart.")
    if stale:
        logger.warning("Marked %d interrupted job(s) as failed.", stale)

    # 3. Initialise Firebase Admin SDK
    #    Wrapped in try/except so the server still starts if the service
    #    account file is missing (useful for running unit tests without creds).
    try:
        import json  # noqa: PLC0415

        import firebase_admin  # noqa: PLC0415
        from firebase_admin import credentials  # noqa: PLC0415

        if not firebase_admin._apps:  # avoid re-initialising in tests
            if settings.firebase_service_account_json:
                cred = credentials.Certificate(
                    json.loads(settings.firebase_service_account_json)
                )
            else:
                cred = credentials.Certificate(settings.firebase_service_account_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialised.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Firebase Admin SDK not initialised: %s", exc)

    if settings.require_firebase:
        import firebase_admin  # noqa: PLC0415

        if not firebase_admin._apps:
            raise RuntimeError(
                "REQUIRE_FIREBASE is set but Firebase Admin SDK is not initialised."
            )

    # 4. Load SRGAN model singleton
    #    Also deferred — skipped gracefully if weights are absent.
    try:
        from services.srgan import load_model  # noqa: PLC0415

        load_model()
        logger.info("SRGAN model loaded.")
    except Exception as exc:  # noqa: BLE001
        logger.warning("SRGAN model could not be loaded at startup: %s", exc)
        if settings.require_model:
            raise

    if settings.require_model:
        from services.srgan import is_loaded  # noqa: PLC0415

        if not is_loaded():
            raise RuntimeError(
                "REQUIRE_MODEL is set but no SRGAN weights were loaded."
            )

    yield  # ---- Application runs here ----

    # ---- SHUTDOWN ----------------------------------------------------------
    logger.info("NeuralLens backend shutting down.")
    from db.session import engine, fail_interrupted_jobs  # noqa: PLC0415

    # uvicorn has already waited for in-flight requests (up to its graceful
    # timeout); anything still unfinished will never complete.
    try:
        left = await fail_interrupted_jobs("Interrupted by server shutdown.")
        if left:
            logger.warning("Marked %d unfinished job(s) as failed.", left)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not clean up unfinished jobs: %s", exc)

    await engine.dispose()


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    """Construct and configure the FastAPI application instance."""

    from middleware.logging import StructlogMiddleware  # noqa: PLC0415

    application = FastAPI(
        title="NeuralLens API",
        description="AI-Powered Image Super-Resolution — Backend API",
        version=settings.app_version,
        # Interactive API docs only in debug; they expose the full surface.
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )

    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @application.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )

    # Middleware: the LAST one added is the outermost.
    # Innermost, so an oversized body is rejected as an ordinary logged 413.
    application.add_middleware(
        BodySizeLimitMiddleware,
        max_bytes=settings.max_upload_bytes + MULTIPART_OVERHEAD,
    )
    application.add_middleware(StructlogMiddleware)
    application.add_middleware(SlowAPIMiddleware)  # applies the default limit

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Outermost, so every response (including CORS and 413s) carries the headers.
    # The strict CSP would break the Swagger UI, so it is off in debug.
    application.add_middleware(
        SecurityHeadersMiddleware, strict_csp=not settings.debug
    )

    # Routers (registered once the modules exist — stubs registered now)
    # Each router is imported lazily so that missing optional deps don't
    # crash the import at startup during early development stages.
    _register_routers(application)

    return application


def _register_routers(application: FastAPI) -> None:
    """Register all API routers onto the application."""

    try:
        from routers import enhance, history, profile, results  # noqa: PLC0415

        application.include_router(enhance.router, prefix="/api", tags=["enhance"])
        application.include_router(history.router, prefix="/api", tags=["history"])
        application.include_router(profile.router, prefix="/api", tags=["profile"])
        application.include_router(results.router, prefix="/api", tags=["results"])
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
@limiter.exempt
async def health_check() -> dict[str, str]:
    """Return a simple liveness confirmation.

    Used by load balancers, uptime monitors, and CI smoke tests.
    No authentication required.
    """
    return {"status": "ok", "version": settings.app_version}


# ---------------------------------------------------------------------------
# Readiness check — verifies DB, model and Firebase; returns 503 otherwise
# ---------------------------------------------------------------------------
@app.get("/ready", tags=["health"], summary="Readiness check")
@limiter.exempt
async def readiness_check() -> JSONResponse:
    """Report whether the service can actually serve enhancement requests."""
    from sqlalchemy import text  # noqa: PLC0415

    from db.session import engine  # noqa: PLC0415
    from services.srgan import is_loaded  # noqa: PLC0415

    import firebase_admin  # noqa: PLC0415

    checks: dict[str, bool] = {
        "model": is_loaded(),
        "firebase": bool(firebase_admin._apps),
    }
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Readiness DB check failed: %s", exc)
        checks["database"] = False

    ok = all(checks.values())
    return JSONResponse(
        status_code=200 if ok else 503,
        content={"status": "ready" if ok else "unavailable", "checks": checks},
    )
