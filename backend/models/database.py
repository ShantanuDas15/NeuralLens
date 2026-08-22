"""NeuralLens — SQLAlchemy ORM models.

Defines the declarative Base and all 5 production-grade tables:
    User, ModelConfig, EnhancementJob, UserUsageStats, AuditLog

Full column specifications match DATABASE_DESIGN.md exactly.
Full implementation completed in Milestone 1.2.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

try:
    from sqlalchemy import JSON
except ImportError:  # pragma: no cover
    from sqlalchemy import Text as JSON  # type: ignore[assignment]


def _now() -> datetime:
    """Return current UTC datetime (used as column default)."""
    return datetime.now(timezone.utc)


def _uuid() -> str:
    """Return a new UUID4 string (used as PK default)."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


# ---------------------------------------------------------------------------
# Table 1: users
# ---------------------------------------------------------------------------


class User(Base):
    """Local projection of a Firebase Auth user.

    Created (or updated) on every verified API request.
    Firebase remains the single source of truth for credentials.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    firebase_uid: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(320), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    auth_provider: Mapped[str] = mapped_column(
        String(32), nullable=False, default="email"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )

    # Relationships
    jobs: Mapped[list["EnhancementJob"]] = relationship(
        "EnhancementJob", back_populates="user"
    )
    usage_stats: Mapped["UserUsageStats | None"] = relationship(
        "UserUsageStats", back_populates="user", uselist=False
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )


# ---------------------------------------------------------------------------
# Table 2: model_configs
# ---------------------------------------------------------------------------


class ModelConfig(Base):
    """Registry of available SR model variants.

    Decouples the model name from job records and enables dynamic
    model switching without schema changes.
    """

    __tablename__ = "model_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    scale_factor: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    weights_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    # Relationships
    jobs: Mapped[list["EnhancementJob"]] = relationship(
        "EnhancementJob", back_populates="model_config"
    )


# ---------------------------------------------------------------------------
# Table 3: enhancement_jobs
# ---------------------------------------------------------------------------


class EnhancementJob(Base):
    """One row per image enhancement request.

    Tracks the full lifecycle: pending → processing → completed | failed.
    """

    __tablename__ = "enhancement_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    model_config_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("model_configs.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="pending", index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    input_file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    input_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    input_width: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    input_height: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    input_format: Mapped[str] = mapped_column(String(8), nullable=False)
    output_file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    output_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_width: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    output_height: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    scale_factor: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=4)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="jobs")
    model_config: Mapped["ModelConfig"] = relationship(
        "ModelConfig", back_populates="jobs"
    )


# ---------------------------------------------------------------------------
# Table 4: user_usage_stats
# ---------------------------------------------------------------------------


class UserUsageStats(Base):
    """Pre-aggregated per-user counters.

    Maintained via application logic (incremented on job state transitions)
    to avoid expensive COUNT(*) aggregations on profile page load.
    """

    __tablename__ = "user_usage_stats"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), unique=True, nullable=False
    )
    total_jobs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    successful_jobs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_jobs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_input_bytes: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0
    )
    total_output_bytes: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0
    )
    last_job_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="usage_stats")


# ---------------------------------------------------------------------------
# Table 5: audit_logs
# ---------------------------------------------------------------------------


class AuditLog(Base):
    """Append-only security and operational event log.

    Rows are NEVER updated or deleted. created_at is the sole timestamp.
    """

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, index=True
    )
    # NOTE: No updated_at — audit_logs are immutable by design.

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")
