"""Test isolation: never let the suite touch a developer's real database.

Several test modules call ``Base.metadata.drop_all`` on teardown. Without this
file they ran against whatever DATABASE_URL the local .env points at (the dev
``neurallens.db``) and wiped it. Environment variables take precedence over
.env in pydantic-settings, so forcing the URL here — before any test module
imports ``config`` or ``db.session`` — keeps every test on in-memory SQLite.
"""

import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ.setdefault("FIREBASE_PROJECT_ID", "test-project")
os.environ.setdefault("FIREBASE_SERVICE_ACCOUNT_PATH", "unused.json")
os.environ.setdefault("DEFAULT_RATE_LIMIT", "")  # suite shares one client IP
