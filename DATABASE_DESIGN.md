# NeuralLens — Database Design
### Senior Principal Architect · Production-Grade Specification

---

## Design Philosophy & Principles

> These principles govern every table, column, and index decision in this schema.

| Principle | Applied As |
|-----------|-----------|
| **UUID Primary Keys** | All PKs use `UUID` (not serial integers) — safe for distributed systems, sharding, and future horizontal scaling |
| **Immutable Audit Trail** | Every table carries `created_at` and `updated_at` timestamps, managed automatically by the ORM |
| **Soft Deletes** | Rows are never hard-deleted. A `deleted_at` timestamp column marks logical deletion. Preserves referential integrity and audit history |
| **Explicit Status Enums** | Job status is stored as a controlled string enum (`pending`, `processing`, `completed`, `failed`) — never a raw integer code |
| **Nullable Foreign Keys** | Firebase manages identity; our `users` table is a local projection. All auth data lives in Firebase; local DB supplements it |
| **Separation of Concerns** | File storage metadata (path, size, dimensions) is separated from processing metadata (model, scale, timing) |
| **Forward Compatibility** | All tables include extensible `meta` JSON column (Phase 2 ready) for unstructured, app-specific flags without schema migrations |
| **ORM Agnostic Types** | Only standard SQL types used — no SQLite-specific syntax — ensuring clean migration to PostgreSQL |
| **Indexing Strategy** | Only index columns that appear in `WHERE`, `ORDER BY`, or `JOIN` clauses in real queries |

---

## Entity Relationship Diagram

```mermaid
erDiagram
    USERS {
        UUID id PK
        STRING firebase_uid UK
        STRING email UK
        STRING display_name
        STRING photo_url
        STRING auth_provider
        BOOLEAN is_active
        BOOLEAN is_verified
        DATETIME last_login_at
        DATETIME created_at
        DATETIME updated_at
        DATETIME deleted_at
    }

    ENHANCEMENT_JOBS {
        UUID id PK
        UUID user_id FK
        UUID model_config_id FK
        STRING status
        STRING original_filename
        STRING input_file_path
        INTEGER input_size_bytes
        INTEGER input_width
        INTEGER input_height
        STRING input_format
        STRING output_file_path
        INTEGER output_size_bytes
        INTEGER output_width
        INTEGER output_height
        INTEGER scale_factor
        INTEGER processing_time_ms
        STRING error_message
        DATETIME completed_at
        DATETIME created_at
        DATETIME updated_at
        DATETIME deleted_at
        JSON meta
    }

    MODEL_CONFIGS {
        UUID id PK
        STRING name UK
        STRING version
        INTEGER scale_factor
        STRING weights_filename
        BOOLEAN is_active
        STRING description
        DATETIME created_at
        DATETIME updated_at
    }

    USER_USAGE_STATS {
        UUID id PK
        UUID user_id FK UK
        INTEGER total_jobs
        INTEGER successful_jobs
        INTEGER failed_jobs
        BIGINT total_input_bytes
        BIGINT total_output_bytes
        DATETIME last_job_at
        DATETIME updated_at
    }

    AUDIT_LOGS {
        UUID id PK
        UUID user_id FK
        STRING action
        STRING resource_type
        UUID resource_id
        STRING ip_address
        STRING user_agent
        JSON payload
        DATETIME created_at
    }

    USERS ||--o{ ENHANCEMENT_JOBS : "submits"
    USERS ||--|| USER_USAGE_STATS : "has"
    USERS ||--o{ AUDIT_LOGS : "generates"
    MODEL_CONFIGS ||--o{ ENHANCEMENT_JOBS : "processes with"
```

---

## Table Definitions

---

### Table 1: `users`

**Purpose:** Local projection of the Firebase Auth user. Created automatically on first authenticated API call (upsert). Stores display metadata and account state. Firebase remains the single source of truth for credentials.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_uuid()` | Internal surrogate key, used for all FK relationships |
| `firebase_uid` | `VARCHAR(128)` | `UNIQUE`, `NOT NULL`, `INDEX` | Firebase Auth UID (e.g. `"abc123xyz"`) — the lookup key on every authenticated request |
| `email` | `VARCHAR(320)` | `UNIQUE`, `NOT NULL`, `INDEX` | Normalized lowercase email. Max 320 chars per RFC 5321 |
| `display_name` | `VARCHAR(255)` | `NULLABLE` | Full name from Firebase profile (e.g. Google display name) |
| `photo_url` | `TEXT` | `NULLABLE` | Profile picture URL from OAuth provider — external CDN link |
| `auth_provider` | `VARCHAR(32)` | `NOT NULL`, `DEFAULT 'email'` | Values: `'google'`, `'email'`. Extensible for future providers |
| `is_active` | `BOOLEAN` | `NOT NULL`, `DEFAULT TRUE` | Account active flag. Set to `FALSE` to soft-suspend a user |
| `is_verified` | `BOOLEAN` | `NOT NULL`, `DEFAULT FALSE` | Email verification status (synced from Firebase) |
| `last_login_at` | `TIMESTAMP WITH TZ` | `NULLABLE` | Updated on every successful API token verification |
| `created_at` | `TIMESTAMP WITH TZ` | `NOT NULL`, `DEFAULT NOW()` | Row creation timestamp — immutable |
| `updated_at` | `TIMESTAMP WITH TZ` | `NOT NULL`, `DEFAULT NOW()` | Auto-updated by ORM `onupdate` hook on any column change |
| `deleted_at` | `TIMESTAMP WITH TZ` | `NULLABLE` | Soft-delete. `NULL` = active. Non-null = logically deleted |

**Indexes:**
```sql
CREATE UNIQUE INDEX idx_users_firebase_uid ON users(firebase_uid);
CREATE UNIQUE INDEX idx_users_email       ON users(email);
CREATE INDEX        idx_users_is_active   ON users(is_active);
CREATE INDEX        idx_users_deleted_at  ON users(deleted_at);
```

**Key Decisions:**
- No password hash stored here — Firebase owns credentials entirely
- `firebase_uid` is the auth bridge: every API call resolves `firebase_uid → users.id` in one indexed lookup
- Soft deletes via `deleted_at` prevent cascade breakage on `enhancement_jobs` when a user "deletes" their account

---

### Table 2: `model_configs`

**Purpose:** Registry of all SR model variants available in the system. Decouples the `enhancement_jobs` table from hardcoded model names. Enables dynamic model switching, versioning, and A/B testing without schema changes.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_uuid()` | Surrogate key |
| `name` | `VARCHAR(128)` | `UNIQUE`, `NOT NULL` | Human-readable identifier e.g. `"real-esrgan-x4plus"` |
| `version` | `VARCHAR(32)` | `NOT NULL` | Semantic version string e.g. `"1.0.0"` |
| `scale_factor` | `SMALLINT` | `NOT NULL` | Upscaling multiplier: `2`, `4`, or `8` |
| `weights_filename` | `VARCHAR(255)` | `NOT NULL` | Weights file name relative to `backend/weights/` dir |
| `is_active` | `BOOLEAN` | `NOT NULL`, `DEFAULT TRUE` | Whether this model is available for new jobs |
| `description` | `TEXT` | `NULLABLE` | Human-readable notes about this model variant |
| `created_at` | `TIMESTAMP WITH TZ` | `NOT NULL`, `DEFAULT NOW()` | Immutable creation timestamp |
| `updated_at` | `TIMESTAMP WITH TZ` | `NOT NULL`, `DEFAULT NOW()` | Auto-updated on any column change |

**Indexes:**
```sql
CREATE UNIQUE INDEX idx_model_configs_name      ON model_configs(name);
CREATE INDEX        idx_model_configs_is_active ON model_configs(is_active);
```

**Seed Data (inserted at migration time):**
```sql
INSERT INTO model_configs (id, name, version, scale_factor, weights_filename, is_active, description)
VALUES (
  gen_uuid(),
  'real-esrgan-x4plus',
  '1.0.0',
  4,
  'RealESRGAN_x4plus.pth',
  TRUE,
  'Default 4x upscaling model. General purpose photorealistic SR.'
);
```

---

### Table 3: `enhancement_jobs`

**Purpose:** The core operational table. Every image enhancement request creates exactly one row here. Tracks the full lifecycle of a job from submission to completion (or failure), with all associated file metadata.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_uuid()` | Surrogate key — also used as the job ID in API responses |
| `user_id` | `UUID` | `NOT NULL`, `FK → users.id`, `INDEX` | Owner of this job |
| `model_config_id` | `UUID` | `NOT NULL`, `FK → model_configs.id` | Which model processed this job |
| `status` | `VARCHAR(16)` | `NOT NULL`, `DEFAULT 'pending'`, `INDEX` | Job lifecycle state. See Status FSM below |
| `original_filename` | `VARCHAR(255)` | `NOT NULL` | The user-supplied filename as uploaded (sanitized) |
| `input_file_path` | `VARCHAR(512)` | `NOT NULL` | Relative server path to the stored LR image |
| `input_size_bytes` | `INTEGER` | `NOT NULL` | File size of original upload in bytes |
| `input_width` | `SMALLINT` | `NOT NULL` | Width of input image in pixels |
| `input_height` | `SMALLINT` | `NOT NULL` | Height of input image in pixels |
| `input_format` | `VARCHAR(8)` | `NOT NULL` | Normalized format string: `'jpeg'` or `'png'` |
| `output_file_path` | `VARCHAR(512)` | `NULLABLE` | Relative server path to the SR result image. `NULL` until `completed` |
| `output_size_bytes` | `INTEGER` | `NULLABLE` | File size of the SR output |
| `output_width` | `SMALLINT` | `NULLABLE` | Width of output image in pixels |
| `output_height` | `SMALLINT` | `NULLABLE` | Height of output image in pixels |
| `scale_factor` | `SMALLINT` | `NOT NULL`, `DEFAULT 4` | The upscaling factor used (denormalized from model_config for query speed) |
| `processing_time_ms` | `INTEGER` | `NULLABLE` | Wall-clock inference time in milliseconds. `NULL` until `completed` |
| `error_message` | `TEXT` | `NULLABLE` | Human-readable error detail if `status = 'failed'` |
| `completed_at` | `TIMESTAMP WITH TZ` | `NULLABLE` | Timestamp of job completion or failure |
| `created_at` | `TIMESTAMP WITH TZ` | `NOT NULL`, `DEFAULT NOW()` | Job submission timestamp |
| `updated_at` | `TIMESTAMP WITH TZ` | `NOT NULL`, `DEFAULT NOW()` | Last state change timestamp |
| `deleted_at` | `TIMESTAMP WITH TZ` | `NULLABLE` | Soft-delete (user removes from history) |
| `meta` | `JSON` | `NULLABLE` | Extensible bag for future unstructured data (e.g. batch ID, tags) |

**Indexes:**
```sql
CREATE INDEX idx_jobs_user_id    ON enhancement_jobs(user_id);
CREATE INDEX idx_jobs_status     ON enhancement_jobs(status);
CREATE INDEX idx_jobs_created_at ON enhancement_jobs(created_at DESC);
CREATE INDEX idx_jobs_deleted_at ON enhancement_jobs(deleted_at);

-- Composite: primary query pattern (user history, newest first, excluding deleted)
CREATE INDEX idx_jobs_user_active_history
    ON enhancement_jobs(user_id, deleted_at, created_at DESC);
```

**Job Status Finite State Machine:**

```
         ┌──────────┐
  Upload  │          │
 ────────►│ pending  │
          │          │
          └────┬─────┘
               │  Model loaded, inference starts
               ▼
          ┌──────────────┐
          │  processing  │
          └──────┬───┬───┘
                 │   │
       Success   │   │  Error / Exception
                 ▼   ▼
          ┌─────────┐  ┌────────┐
          │completed│  │ failed │
          └─────────┘  └────────┘
```

**Key Decisions:**
- `scale_factor` is denormalized from `model_configs` for query performance — avoids a JOIN on every history list call
- Input dimensions stored pre-processing, output dimensions stored post-processing — enables compression ratio analytics
- `meta` JSON column allows Phase 2 features (batch IDs, user tags, retry count) without adding new columns

---

### Table 4: `user_usage_stats`

**Purpose:** A pre-aggregated summary row per user, maintained via application logic (incremented on job state transitions). Avoids expensive `COUNT(*)` and `SUM()` queries on `enhancement_jobs` for every profile page load. Critical for scalability when job counts grow into thousands.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_uuid()` | Surrogate key |
| `user_id` | `UUID` | `UNIQUE`, `NOT NULL`, `FK → users.id` | One row per user — enforced by UNIQUE constraint |
| `total_jobs` | `INTEGER` | `NOT NULL`, `DEFAULT 0` | Lifetime count of submitted jobs |
| `successful_jobs` | `INTEGER` | `NOT NULL`, `DEFAULT 0` | Count of `completed` jobs |
| `failed_jobs` | `INTEGER` | `NOT NULL`, `DEFAULT 0` | Count of `failed` jobs |
| `total_input_bytes` | `BIGINT` | `NOT NULL`, `DEFAULT 0` | Cumulative bytes uploaded by this user |
| `total_output_bytes` | `BIGINT` | `NOT NULL`, `DEFAULT 0` | Cumulative bytes of SR output generated |
| `last_job_at` | `TIMESTAMP WITH TZ` | `NULLABLE` | Timestamp of the user's most recent job |
| `updated_at` | `TIMESTAMP WITH TZ` | `NOT NULL`, `DEFAULT NOW()` | Auto-updated on every stat change |

**Indexes:**
```sql
CREATE UNIQUE INDEX idx_usage_stats_user_id ON user_usage_stats(user_id);
```

**Write Pattern:**
Stats are updated in the same database transaction that updates a job's status. This ensures stats are always consistent with job records — never stale or out-of-sync.

---

### Table 5: `audit_logs`

**Purpose:** Append-only log of security-relevant and operationally significant events. Used for debugging, compliance, anomaly detection, and forensic analysis. Rows are **never updated or deleted**.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | `PRIMARY KEY`, `DEFAULT gen_uuid()` | Surrogate key |
| `user_id` | `UUID` | `NULLABLE`, `FK → users.id`, `INDEX` | Actor who triggered the event. `NULL` for unauthenticated events |
| `action` | `VARCHAR(64)` | `NOT NULL`, `INDEX` | Event type. See Action Catalogue below |
| `resource_type` | `VARCHAR(64)` | `NULLABLE` | Entity class affected e.g. `'enhancement_job'`, `'user'` |
| `resource_id` | `UUID` | `NULLABLE` | UUID of the affected entity row |
| `ip_address` | `VARCHAR(45)` | `NULLABLE` | IPv4 or IPv6 address of the client |
| `user_agent` | `TEXT` | `NULLABLE` | Full browser user-agent string |
| `payload` | `JSON` | `NULLABLE` | Contextual data specific to the action type |
| `created_at` | `TIMESTAMP WITH TZ` | `NOT NULL`, `DEFAULT NOW()` | Immutable. Row is never updated |

**Indexes:**
```sql
CREATE INDEX idx_audit_logs_user_id    ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action     ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
```

**Action Catalogue (Phase 1):**

| Action | Trigger |
|--------|---------|
| `user.created` | New user upserted from Firebase token |
| `user.login` | Successful token verification on any API call |
| `user.deleted` | User account soft-deleted |
| `job.submitted` | `POST /api/enhance` received |
| `job.completed` | SRGAN inference succeeded |
| `job.failed` | SRGAN inference threw an exception |
| `job.deleted` | User removed a job from history |
| `profile.viewed` | `GET /api/profile` called |

---

## Data Flow Per Feature

### Feature: Image Enhancement (`POST /api/enhance`)

```
1.  FastAPI receives multipart/form-data upload
2.  Middleware: firebase_uid extracted from Bearer token
3.  DB: SELECT id FROM users WHERE firebase_uid = :uid  (indexed)
4.  DB: INSERT INTO enhancement_jobs
        (user_id, model_config_id, status='pending', original_filename, input_*) → returns job.id
5.  DB: UPDATE user_usage_stats SET total_jobs += 1 WHERE user_id = :uid
6.  DB: INSERT INTO audit_logs (action='job.submitted', resource_id=job.id)
7.  Image saved to disk: uploads/{user_id}/{job_id}.{ext}
8.  DB: UPDATE enhancement_jobs SET status='processing' WHERE id = :job_id
9.  PyTorch inference runs
10. Output saved to disk: results/{user_id}/{job_id}.{ext}
11. DB: UPDATE enhancement_jobs SET
          status='completed',
          output_file_path=...,
          output_size_bytes=...,
          output_width=...,
          output_height=...,
          processing_time_ms=...,
          completed_at=NOW()
      WHERE id = :job_id
12. DB: UPDATE user_usage_stats SET
          successful_jobs += 1,
          total_input_bytes += :input_bytes,
          total_output_bytes += :output_bytes,
          last_job_at = NOW()
      WHERE user_id = :uid
13. DB: INSERT INTO audit_logs (action='job.completed', resource_id=job.id)
14. API response: { job_id, result_url, processing_time_ms }
```

### Feature: Enhancement History (`GET /api/history`)

```sql
-- Primary history query (paginated, newest first, excludes soft-deleted)
SELECT
    ej.id,
    ej.status,
    ej.original_filename,
    ej.input_width,
    ej.input_height,
    ej.output_width,
    ej.output_height,
    ej.scale_factor,
    ej.processing_time_ms,
    ej.created_at,
    ej.completed_at,
    mc.name AS model_name
FROM enhancement_jobs ej
JOIN model_configs mc ON ej.model_config_id = mc.id
WHERE ej.user_id     = :user_id
  AND ej.deleted_at  IS NULL
  AND ej.status      = 'completed'
ORDER BY ej.created_at DESC
LIMIT :page_size OFFSET :offset;
```

Served by: `idx_jobs_user_active_history` composite index.

### Feature: Profile (`GET /api/profile`)

```sql
-- No aggregation query needed — read from pre-computed stats row
SELECT
    u.display_name, u.email, u.photo_url, u.auth_provider,
    u.created_at   AS member_since,
    s.total_jobs,
    s.successful_jobs,
    s.failed_jobs,
    s.last_job_at
FROM users u
LEFT JOIN user_usage_stats s ON s.user_id = u.id
WHERE u.firebase_uid = :firebase_uid
  AND u.deleted_at IS NULL;
```

---

## SQLAlchemy Model Stubs

```python
# backend/models/database.py

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, Integer, SmallInteger,
    BigInteger, Text, JSON, DateTime, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def now_utc():
    return datetime.now(timezone.utc)

def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id              = Column(String(36), primary_key=True, default=gen_uuid)
    firebase_uid    = Column(String(128), unique=True, nullable=False, index=True)
    email           = Column(String(320), unique=True, nullable=False, index=True)
    display_name    = Column(String(255), nullable=True)
    photo_url       = Column(Text, nullable=True)
    auth_provider   = Column(String(32), nullable=False, default="email")
    is_active       = Column(Boolean, nullable=False, default=True)
    is_verified     = Column(Boolean, nullable=False, default=False)
    last_login_at   = Column(DateTime(timezone=True), nullable=True)
    created_at      = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at      = Column(DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)
    deleted_at      = Column(DateTime(timezone=True), nullable=True, index=True)

    jobs            = relationship("EnhancementJob", back_populates="user")
    usage_stats     = relationship("UserUsageStats", back_populates="user", uselist=False)


class ModelConfig(Base):
    __tablename__ = "model_configs"

    id               = Column(String(36), primary_key=True, default=gen_uuid)
    name             = Column(String(128), unique=True, nullable=False)
    version          = Column(String(32), nullable=False)
    scale_factor     = Column(SmallInteger, nullable=False)
    weights_filename = Column(String(255), nullable=False)
    is_active        = Column(Boolean, nullable=False, default=True)
    description      = Column(Text, nullable=True)
    created_at       = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at       = Column(DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)

    jobs             = relationship("EnhancementJob", back_populates="model_config")


class EnhancementJob(Base):
    __tablename__ = "enhancement_jobs"

    id                = Column(String(36), primary_key=True, default=gen_uuid)
    user_id           = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    model_config_id   = Column(String(36), ForeignKey("model_configs.id"), nullable=False)
    status            = Column(String(16), nullable=False, default="pending", index=True)
    original_filename = Column(String(255), nullable=False)
    input_file_path   = Column(String(512), nullable=False)
    input_size_bytes  = Column(Integer, nullable=False)
    input_width       = Column(SmallInteger, nullable=False)
    input_height      = Column(SmallInteger, nullable=False)
    input_format      = Column(String(8), nullable=False)
    output_file_path  = Column(String(512), nullable=True)
    output_size_bytes = Column(Integer, nullable=True)
    output_width      = Column(SmallInteger, nullable=True)
    output_height     = Column(SmallInteger, nullable=True)
    scale_factor      = Column(SmallInteger, nullable=False, default=4)
    processing_time_ms = Column(Integer, nullable=True)
    error_message     = Column(Text, nullable=True)
    completed_at      = Column(DateTime(timezone=True), nullable=True)
    created_at        = Column(DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at        = Column(DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)
    deleted_at        = Column(DateTime(timezone=True), nullable=True, index=True)
    meta              = Column(JSON, nullable=True)

    user              = relationship("User", back_populates="jobs")
    model_config      = relationship("ModelConfig", back_populates="jobs")


class UserUsageStats(Base):
    __tablename__ = "user_usage_stats"

    id                  = Column(String(36), primary_key=True, default=gen_uuid)
    user_id             = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    total_jobs          = Column(Integer, nullable=False, default=0)
    successful_jobs     = Column(Integer, nullable=False, default=0)
    failed_jobs         = Column(Integer, nullable=False, default=0)
    total_input_bytes   = Column(BigInteger, nullable=False, default=0)
    total_output_bytes  = Column(BigInteger, nullable=False, default=0)
    last_job_at         = Column(DateTime(timezone=True), nullable=True)
    updated_at          = Column(DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)

    user                = relationship("User", back_populates="usage_stats")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id            = Column(String(36), primary_key=True, default=gen_uuid)
    user_id       = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action        = Column(String(64), nullable=False, index=True)
    resource_type = Column(String(64), nullable=True)
    resource_id   = Column(String(36), nullable=True)
    ip_address    = Column(String(45), nullable=True)
    user_agent    = Column(Text, nullable=True)
    payload       = Column(JSON, nullable=True)
    created_at    = Column(DateTime(timezone=True), nullable=False, default=now_utc, index=True)
    # NOTE: No updated_at — audit_logs are immutable by design
```

---

## Migration Strategy — SQLite → PostgreSQL

The schema is written to be **engine-neutral** via SQLAlchemy. When migrating:

| Step | Action |
|------|--------|
| 1 | Change `DATABASE_URL` in `.env` from `sqlite:///./neurallens.db` to `postgresql+asyncpg://...` |
| 2 | Add `Alembic` for versioned schema migrations (one command: `alembic init`) |
| 3 | Export SQLite data via `sqlite3 .dump` and import into Postgres |
| 4 | Enable `RETURNING` clauses and `gen_random_uuid()` native to Postgres |
| 5 | Enable connection pooling (`asyncpg` + `pool_size=10`) |

> **Zero schema changes required.** The same model definitions work on both engines.

---

## Phase 2 Scalability Extensions

| Phase 2 Feature | Schema Change Required |
|----------------|----------------------|
| Batch Processing | Add `batch_id UUID` column to `enhancement_jobs` + new `batches` table |
| Scale Factor UI | Already supported — `scale_factor` stored per-job |
| Usage Quotas | Add `monthly_quota INTEGER` and `quota_reset_at TIMESTAMP` to `users` |
| Cloud Storage | Replace `input_file_path` / `output_file_path` with `input_storage_url` / `output_storage_url` — same column, different values |
| Model Comparison | Add `comparison_job_id UUID` FK to `enhancement_jobs` — self-referencing |
| Tags / Labels | Add `tags TEXT[]` to `enhancement_jobs` (PostgreSQL native) or use `meta` JSON |
| Soft Account Deletion GDPR | `deleted_at` already present — add background job to anonymize PII columns |

---

## Summary

| Table | Rows at Scale | Primary Access Pattern |
|-------|--------------|----------------------|
| `users` | ~10K–100K | Lookup by `firebase_uid` per request |
| `model_configs` | ~5–20 | Read once at startup, cached in memory |
| `enhancement_jobs` | ~1M+ | List by `user_id`, ordered by `created_at DESC` |
| `user_usage_stats` | 1 per user | Point lookup by `user_id` for profile page |
| `audit_logs` | ~10M+ | Append-only; read only for investigations |

All primary access patterns are covered by the defined indexes. No table scan queries exist in the Phase 1 application code.
