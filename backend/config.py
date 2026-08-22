"""NeuralLens backend configuration.

Loads all settings from the .env file via pydantic-settings.
Every environment variable is typed and validated at startup.
"""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file."""

    # Firebase
    firebase_project_id: str
    firebase_service_account_path: str

    # Database
    database_url: str = "sqlite+aiosqlite:///./neurallens.db"

    # File storage
    upload_dir: str = "uploads"
    results_dir: str = "results"
    max_upload_bytes: int = 2_097_152  # 2 MB

    # CORS
    allowed_origins: list[str] = ["http://localhost:5173"]

    # Application
    app_version: str = "1.0.0"
    debug: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings singleton.

    Using lru_cache means the .env file is read exactly once per process.
    """
    return Settings()


# Module-level singleton — imported directly by other modules.
settings: Settings = get_settings()
