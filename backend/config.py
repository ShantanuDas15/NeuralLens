"""NeuralLens backend configuration.

Loads all settings from the .env file via pydantic-settings.
Every environment variable is typed and validated at startup.
"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic import field_validator
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

    # Fail startup (instead of only warning) if model weights are missing.
    require_model: bool = False

    # File storage
    upload_dir: str = "uploads"
    results_dir: str = "results"
    max_upload_bytes: int = 2_097_152  # 2 MB

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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings singleton.

    Using lru_cache means the .env file is read exactly once per process.
    """
    return Settings()


# Module-level singleton — imported directly by other modules.
settings: Settings = get_settings()
