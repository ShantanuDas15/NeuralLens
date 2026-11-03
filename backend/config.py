"""NeuralLens backend configuration.

Loads all settings from the .env file via pydantic-settings.
Every environment variable is typed and validated at startup.
"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file."""

    # Firebase
    firebase_project_id: str
    # Either a path to the service-account JSON file, or the JSON itself
    # (e.g. a Railway variable). The JSON variant wins if both are set.
    firebase_service_account_path: str = ""
    firebase_service_account_json: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./neurallens.db"
    # Fail startup if DATABASE_URL is SQLite (set true in production).
    require_postgres: bool = False

    # Fail startup (instead of only warning) if model weights are missing.
    require_model: bool = False
    # Fail startup if Firebase Admin could not be initialised (else every login fails).
    require_firebase: bool = False
    # Jobs allowed in the system at once (1 running + the rest waiting for the slot).
    max_pending_jobs: int = 4

    # File storage
    upload_dir: str = "uploads"
    results_dir: str = "results"
    max_upload_bytes: int = 2_097_152  # 2 MB

    # Inference limits (protect memory: a 2 MB file can decode to a huge image)
    max_input_pixels: int = 4_000_000  # ~2000x2000
    max_output_pixels: int = 50_000_000  # input pixels * scale^2
    tile_size: int = 400  # 0 disables tiling (whole image in one pass)
    queue_timeout_seconds: float = 60.0  # max wait for the single inference slot

    # CORS
    allowed_origins: list[str] = ["http://localhost:5173"]

    # Application
    app_version: str = "1.0.0"
    debug: bool = False

    @field_validator("database_url")
    @classmethod
    def _normalise_database_url(cls, v: str) -> str:
        """Accept provider-style Postgres URLs and force the asyncpg driver."""
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+asyncpg://" + v[len(prefix):]
        return v

    @model_validator(mode="after")
    def _require_postgres_in_production(self) -> "Settings":
        """Refuse to boot on SQLite when REQUIRE_POSTGRES is set.

        SQLite lives on the container's ephemeral disk on Railway, so a
        mis-wired DATABASE_URL would silently lose all data on restart.
        """
        if self.require_postgres and "sqlite" in self.database_url:
            raise ValueError(
                "REQUIRE_POSTGRES is set but DATABASE_URL points at SQLite."
            )
        return self

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings singleton.

    Using lru_cache means the .env file is read exactly once per process.
    """
    return Settings()


# Module-level singleton — imported directly by other modules.
settings: Settings = get_settings()
