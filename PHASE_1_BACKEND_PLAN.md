# NeuralLens — Phase 1 Backend Development Plan
### Backend Infrastructure · Implementation · Validation · Hardening

> **Mandate**: The backend must be fully implemented, all tests passing, and the system hardened before any frontend work begins.
> This document is the single execution guide for Phase 1. Update task checkboxes and commit hashes after each milestone is validated.

---

## System Environment Audit

| Property | Value | Notes |
|----------|-------|-------|
| **OS** | Linux (Ubuntu) | Native CUDA support |
| **CPU** | Intel Core i7-13700HX | 24 threads — fast multi-core preprocessing |
| **RAM** | 14 GB | Sufficient for model + API + DB in parallel |
| **GPU** | NVIDIA GeForce RTX 4060 Laptop | 8 GB VRAM, 7.8 GB free |
| **CUDA** | 13.2 | Requires PyTorch nightly or cu124 wheel |
| **Disk** | 142 GB free / 196 GB total | Ample for weights, uploads, results |
| **Python** | 3.14.4 (system) | Venv will isolate project deps |
| **Git** | Installed | No repo initialized yet |

> **GPU Note**: RTX 4060 with 8 GB VRAM is more than sufficient to run Real-ESRGAN inference at < 1 second per image. CUDA-accelerated inference will be the default.

---

## Current Project Progress

| Artefact | Status |
|---------|--------|
| `PROJECT.md` | ✅ Complete |
| `DATABASE_DESIGN.md` | ✅ Complete |
| `GEMINI.md` | ✅ Complete |
| `backend/` directory | ✅ Scaffold complete (Milestone 1.1) |
| `frontend/` directory | ⏸️ Blocked (backend-first mandate) |
| Git repository | ✅ Initialized (`main` branch) |
| Virtual environment | ✅ Created (`backend/venv/`) |

---

## Complete Dependency Manifest

### Core Runtime
| Package | Pinned Version | Purpose |
|---------|---------------|---------|
| `fastapi` | `>=0.115.0` | Async REST API framework |
| `uvicorn[standard]` | `>=0.30.0` | ASGI server with WebSocket + HTTP2 support |
| `python-multipart` | `>=0.0.9` | Required for FastAPI `UploadFile` (multipart form) |
| `pydantic` | `>=2.7.0` | Request/response data validation (FastAPI v2 native) |
| `pydantic-settings` | `>=2.3.0` | `.env` config loading via `BaseSettings` |
| `python-dotenv` | `>=1.0.0` | `.env` file parsing |

### Database
| Package | Pinned Version | Purpose |
|---------|---------------|---------|
| `sqlalchemy` | `>=2.0.30` | ORM with async support |
| `aiosqlite` | `>=0.20.0` | Async SQLite driver (SQLAlchemy async engine) |

### Authentication
| Package | Pinned Version | Purpose |
|---------|---------------|---------|
| `firebase-admin` | `>=6.5.0` | Firebase Admin SDK — token verification |

### Computer Vision & ML
| Package | Pinned Version | Purpose |
|---------|---------------|---------|
| `torch` | `>=2.3.0+cu124` | PyTorch with CUDA 12.4 support (RTX 4060) |
| `torchvision` | `>=0.18.0+cu124` | Vision transforms, tensor utilities |
| `basicsr` | `>=1.4.2` | Real-ESRGAN base architecture library |
| `realesrgan` | `>=0.3.0` | Real-ESRGAN high-level inference API |
| `opencv-python-headless` | `>=4.10.0` | Image reading, color space conversion (no GUI) |
| `Pillow` | `>=12.1.1` | Image format handling, PNG/JPEG I/O |
| `numpy` | `>=1.26.0` | Array operations between CV and PyTorch |

### Testing
| Package | Pinned Version | Purpose |
|---------|---------------|---------|
| `pytest` | `>=8.2.0` | Test runner |
| `pytest-asyncio` | `>=0.23.0` | Async test support for FastAPI |
| `httpx` | `>=0.27.0` | Async HTTP client — used by FastAPI `TestClient` |
| `pytest-cov` | `>=5.0.0` | Coverage reporting |

### Code Quality
| Package | Pinned Version | Purpose |
|---------|---------------|---------|
| `black` | `>=24.0.0` | PEP 8 auto-formatter |
| `isort` | `>=5.13.0` | Import ordering |

---

## Final Directory Structure (Target)

```
NeuralLens/
├── backend/
│   ├── main.py                     # FastAPI app, lifespan, CORS, router registration
│   ├── config.py                   # Pydantic BaseSettings — loads .env
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── enhance.py              # POST /api/enhance
│   │   ├── history.py              # GET  /api/history
│   │   └── profile.py              # GET  /api/profile
│   ├── services/
│   │   ├── __init__.py
│   │   ├── srgan.py                # Real-ESRGAN singleton + inference
│   │   └── image_utils.py          # OpenCV/Pillow pre & postprocessing
│   ├── models/
│   │   ├── __init__.py
│   │   └── database.py             # SQLAlchemy ORM models (5 tables)
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── enhance.py              # Pydantic request/response schemas
│   │   ├── history.py
│   │   └── profile.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth.py                 # Firebase token verification FastAPI dependency
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py              # SQLAlchemy async engine + session factory
│   ├── weights/
│   │   └── RealESRGAN_x4plus.pth   # Pre-trained weights (gitignored if >100MB)
│   ├── uploads/                    # User LR uploads — {user_id}/{job_id}.ext
│   ├── results/                    # SR outputs — {user_id}/{job_id}.ext
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py             # Shared fixtures, mock DB, mock auth
│   │   ├── test_auth.py            # Token verification tests
│   │   ├── test_enhance.py         # Enhancement endpoint tests
│   │   ├── test_history.py         # History endpoint tests
│   │   └── test_profile.py         # Profile endpoint tests
│   ├── requirements.txt
│   ├── requirements-dev.txt        # Test + lint tools (not in prod)
│   └── .env                        # Never committed
│
├── PROJECT.md
├── DATABASE_DESIGN.md
├── GEMINI.md
├── PHASE_1_BACKEND_PLAN.md         # This file
├── .gitignore
└── README.md
```

---

## Milestone Overview

| # | Milestone | Deliverable | Status |
|---|-----------|-------------|--------|
| **1.1** | Project Scaffold & Environment | Repo, venv, `.gitignore`, `requirements.txt`, `main.py` | `[x] Complete` |
| **1.2** | Database Layer | ORM models, async engine, session factory, migration | `[x] Complete` |
| **1.3** | Auth Middleware | Firebase token verification FastAPI dependency | `[x] Complete` |
| **1.4** | SRGAN Inference Service | Model weights, singleton loader, inference pipeline | `[x] Complete` |
| **1.5** | API Endpoints | `/api/enhance`, `/api/history`, `/api/profile`, `/health` | `[ ]` |

---

---

## Milestone 1.1 — Project Scaffold & Environment

**Goal**: Establish the full project skeleton, virtual environment, dependency manifest, `.gitignore`, and a running FastAPI app that returns a health check.

### Files Created

| File | Action |
|------|--------|
| `.gitignore` | [NEW] Block all secrets, caches, uploads, weights |
| `backend/requirements.txt` | [NEW] Pinned production dependencies |
| `backend/requirements-dev.txt` | [NEW] Test + lint dependencies |
| `backend/config.py` | [NEW] `Settings` class via `pydantic-settings` |
| `backend/main.py` | [NEW] FastAPI app with health check, CORS, lifespan |
| `backend/db/session.py` | [NEW] Async SQLAlchemy engine + `AsyncSession` factory |
| `README.md` | [NEW] Setup and run instructions |

### `config.py` — Settings Contract

```python
# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    firebase_project_id: str
    firebase_service_account_path: str
    database_url: str = "sqlite+aiosqlite:///./neurallens.db"
    upload_dir: str = "uploads"
    results_dir: str = "results"
    max_upload_bytes: int = 2_097_152   # 2 MB
    allowed_origins: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"

settings = Settings()
```

### `.env` Template (never committed)

```dotenv
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_SERVICE_ACCOUNT_PATH=./firebase-service-account.json
DATABASE_URL=sqlite+aiosqlite:///./neurallens.db
UPLOAD_DIR=uploads
RESULTS_DIR=results
MAX_UPLOAD_BYTES=2097152
```

### `main.py` — App Bootstrap

```python
# Registers: CORS, lifespan (model load + DB init), /health, all routers
# CORS origins: loaded from settings.allowed_origins
# Lifespan: creates DB tables, loads SRGAN singleton
```

### Verification Gateway

```bash
# From backend/ with venv active:
uvicorn main:app --reload --port 8000

# Expected response:
curl http://localhost:8000/health
# → {"status": "ok", "version": "1.0.0"}

# Swagger docs accessible at:
# http://localhost:8000/docs
```

### Completion Checklist
- `[x]` Virtual environment created (`python3 -m venv venv`)
- `[x]` All packages installed from `requirements.txt`
- `[x]` `.gitignore` verified (no `.env`, no `*.db`, no `uploads/`, no `weights/*.pth`)
- `[x]` `config.py` loads from `.env` without error
- `[x]` `GET /health` returns `{"status": "ok"}` with HTTP 200 — **10/10 tests PASSED**
- `[x]` Git repo initialized, first commit on `main`
- `[x]` `black` + `isort`: zero violations

**Commit**: `feat: Implement Milestone 1.1 — Project scaffold, venv, health endpoint`
**Commit Hash**: `92c5f3c`

---

---

## Milestone 1.2 — Database Layer

**Goal**: Define all 5 SQLAlchemy ORM models, create the async database session factory, run the table migration, and seed the `model_configs` table with the Real-ESRGAN entry.

### Files Created / Modified

| File | Action |
|------|--------|
| `backend/models/database.py` | [NEW] All 5 ORM model classes |
| `backend/db/session.py` | [MODIFY] Add `init_db()` + session dependency |

### 5 ORM Models to Implement

```
User               → users table
ModelConfig        → model_configs table
EnhancementJob     → enhancement_jobs table
UserUsageStats     → user_usage_stats table
AuditLog           → audit_logs table
```

Full column specifications are defined in `DATABASE_DESIGN.md`. Implementation must match exactly.

### `db/session.py` — Session Factory Contract

```python
# Exposes:
#   engine: AsyncEngine
#   AsyncSessionLocal: async_sessionmaker
#   get_db() -> AsyncGenerator[AsyncSession, None]   # FastAPI dependency
#   init_db() -> None                                # Creates all tables + seeds model_configs
```

### Seed Data (runs inside `init_db()`)

```python
# Insert default model config if not exists:
{
  "name": "real-esrgan-x4plus",
  "version": "1.0.0",
  "scale_factor": 4,
  "weights_filename": "RealESRGAN_x4plus.pth",
  "is_active": True,
  "description": "Default 4x upscaling. General purpose photorealistic SR."
}
```

### Tests — `tests/test_db.py`

```python
# Test 1: init_db() creates all 5 tables without error (in-memory SQLite)
# Test 2: ModelConfig seed row is inserted exactly once (idempotent)
# Test 3: User row can be inserted, retrieved by firebase_uid, and soft-deleted
# Test 4: EnhancementJob FK constraint enforced — job without valid user_id raises IntegrityError
# Test 5: UserUsageStats unique constraint on user_id — second insert raises IntegrityError
# Test 6: AuditLog row inserted and created_at is immutable (no updated_at column)
# All tests use in-memory: sqlite+aiosqlite:///:memory:
```

### Verification Gateway

```bash
pytest backend/tests/test_db.py -v
# All 6 tests must PASS

# Manual spot check — inspect the DB file:
python3 -c "
import sqlite3, asyncio
from db.session import init_db
asyncio.run(init_db())
conn = sqlite3.connect('neurallens.db')
print(conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall())
print(conn.execute('SELECT name, version, scale_factor FROM model_configs').fetchall())
conn.close()
"
# Expected: 5 table names + 1 model_config row
```

### Completion Checklist
- `[x]` All 5 ORM models match `DATABASE_DESIGN.md` column-for-column
- `[x]` `init_db()` creates tables without error on fresh run
- `[x]` `init_db()` is idempotent — safe to call multiple times
- `[x]` `model_configs` seed row present after init
- `[x]` All 6 DB tests pass with `pytest`
- `[x]` No `.db` file committed to git

**Commit**: `feat: Implement Milestone 1.2 — SQLAlchemy ORM models and async DB session`
**Commit Hash**: `67322c8`

---

---

## Milestone 1.3 — Firebase Auth Middleware

**Goal**: Implement a FastAPI dependency that verifies Firebase ID tokens on every protected route, extracts the user's `firebase_uid` and `email`, and performs an upsert into the `users` table on every verified request.

### Files Created

| File | Action |
|------|--------|
| `backend/middleware/auth.py` | [NEW] `get_current_user()` FastAPI dependency |

### `auth.py` — Dependency Contract

```python
# Function signature:
async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
) -> User:

# Behaviour:
# 1. Extract token from "Bearer <token>" header
# 2. Call firebase_admin.auth.verify_id_token(token)
# 3. On invalid/expired token → raise HTTPException(401)
# 4. Extract uid and email from decoded token
# 5. Upsert user row (INSERT if new, UPDATE last_login_at if exists)
# 6. Upsert user_usage_stats row (INSERT with zeros if first login)
# 7. INSERT audit_log row with action="user.login"
# 8. Return the User ORM object
```

### Firebase Admin SDK Initialization

```python
# backend/main.py lifespan — initialize once at startup:
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate(settings.firebase_service_account_path)
firebase_admin.initialize_app(cred)
```

### Tests — `tests/test_auth.py`

```python
# Fixture: mock firebase_admin.auth.verify_id_token to return a fake decoded token
# Mock decoded token: {"uid": "test-uid-001", "email": "test@neurallens.com"}

# Test 1: Valid mock token → returns User object with correct firebase_uid
# Test 2: Valid token → user row upserted in DB (check firebase_uid exists)
# Test 3: Valid token second call → no duplicate user row (upsert idempotent)
# Test 4: Missing Authorization header → HTTP 422 (Unprocessable Entity)
# Test 5: Malformed "Bearer" prefix → HTTP 401
# Test 6: Expired/invalid token (mock raises InvalidIdTokenError) → HTTP 401
# Test 7: Revoked token (mock raises RevokedIdTokenError) → HTTP 401
# Test 8: audit_logs row with action="user.login" written on successful auth
```

### Verification Gateway

```bash
pytest backend/tests/test_auth.py -v
# All 8 tests must PASS — zero live Firebase calls (all mocked)

# Manual integration test (requires real Firebase project + service account):
TOKEN=$(curl -s "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=YOUR_WEB_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"testpass","returnSecureToken":true}' | jq -r .idToken)

curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/profile
# → 200 OK (or 404 if profile not yet implemented — not 401)
```

### Completion Checklist
- `[x]` Firebase Admin SDK initializes cleanly from `.env` path
- `[x]` `get_current_user()` dependency resolves correctly on valid token
- `[x]` User upsert is idempotent — no duplicate rows
- `[x]` `user_usage_stats` row created on first login
- `[x]` `audit_logs` entry written on every login
- `[x]` All 8 auth tests pass with mocked Firebase

**Commit**: `feat: Implement Milestone 1.3 — Firebase auth middleware with user upsert`
**Commit Hash**: `8808b64`

---

---

## Milestone 1.4 — SRGAN Inference Service

**Goal**: Download Real-ESRGAN pre-trained weights, implement a singleton model loader that runs at app startup, and build the inference pipeline that accepts a raw image bytes input and returns an upscaled image as bytes.

### Files Created

| File | Action |
|------|--------|
| `backend/services/srgan.py` | [NEW] Model singleton + `enhance_image()` |
| `backend/services/image_utils.py` | [NEW] Preprocess + postprocess helpers |
| `backend/weights/RealESRGAN_x4plus.pth` | [DOWNLOAD] Pre-trained weights |

### Model Download

```bash
# Download Real-ESRGAN x4plus weights (~65 MB):
mkdir -p backend/weights
wget -O backend/weights/RealESRGAN_x4plus.pth \
  "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
```

### `srgan.py` — Singleton Contract

```python
# Module-level singleton: _model_instance: RealESRGANer | None = None

# Function: load_model() -> None
#   Called once during FastAPI lifespan startup
#   Loads weights from settings.weights_path
#   Selects device: "cuda" if torch.cuda.is_available() else "cpu"
#   Logs: "SRGAN model loaded on {device}" at INFO level

# Function: enhance_image(input_bytes: bytes) -> tuple[bytes, dict]
#   Returns: (sr_image_bytes_as_png, metadata_dict)
#   metadata_dict keys: input_width, input_height, output_width, output_height, processing_time_ms
#   Raises: ValueError on corrupt/unreadable image input
#   Raises: RuntimeError if model is not loaded (load_model() not called)
```

### `image_utils.py` — Preprocessing Contract

```python
# Function: validate_and_decode(raw_bytes: bytes, max_bytes: int) -> np.ndarray
#   Validates file size ≤ max_bytes
#   Decodes bytes → OpenCV BGR numpy array
#   Raises: ValueError if size exceeded, format unreadable, or image is corrupt

# Function: encode_to_png(bgr_array: np.ndarray) -> bytes
#   Encodes BGR numpy array → PNG bytes
#   Returns raw bytes suitable for writing to disk
```

### Tests — `tests/test_srgan.py`

```python
# All tests mock the actual RealESRGANer.enhance() call to return a fake
# numpy array — no GPU required in test suite.

# Test 1: load_model() succeeds and sets the singleton (mock weights load)
# Test 2: enhance_image() called before load_model() raises RuntimeError
# Test 3: enhance_image() with valid 64x64 PNG bytes → returns bytes + metadata dict
# Test 4: metadata dict contains correct keys: input_width, input_height, output_width,
#          output_height, processing_time_ms
# Test 5: output_width = input_width * 4, output_height = input_height * 4
# Test 6: validate_and_decode() with oversized bytes raises ValueError
# Test 7: validate_and_decode() with corrupt non-image bytes raises ValueError
# Test 8: validate_and_decode() with valid JPEG bytes → returns numpy array of correct shape
```

### Verification Gateway

```bash
pytest backend/tests/test_srgan.py -v
# All 8 tests PASS (mocked inference — no GPU needed for tests)

# Manual end-to-end inference check (requires weights downloaded):
python3 -c "
import asyncio, pathlib
from services.srgan import load_model, enhance_image
from config import settings
load_model()
img_bytes = pathlib.Path('tests/fixtures/sample_lr.png').read_bytes()
result_bytes, meta = enhance_image(img_bytes)
print('Input:', meta['input_width'], 'x', meta['input_height'])
print('Output:', meta['output_width'], 'x', meta['output_height'])
print('Time:', meta['processing_time_ms'], 'ms')
print('Result size:', len(result_bytes), 'bytes')
"
# Expected: output dimensions = 4× input, time < 2000ms on RTX 4060
```

### Completion Checklist
- `[x]` Weights downloaded and present at `backend/weights/RealESRGAN_x4plus.pth`
- `[x]` `weights/` directory in `.gitignore` (or Git LFS if >100MB)
- `[x]` Model loads on CUDA without error (RTX 4060)
- `[x]` `enhance_image()` returns correct 4× dimensions
- `[x]` Validate function correctly blocks corrupt or oversized uploads
- `[x]` 8/8 mocked validation tests passing

**Commit**: `feat: Implement Milestone 1.4 — SRGAN Inference Service`
**Commit Hash**: `6f35025`

---

---

## Milestone 1.5 — API Endpoints

**Goal**: Implement all four production API endpoints. Each endpoint must handle auth, validation, database writes, error handling, and return well-structured JSON responses per the Pydantic schemas.

### Files Created / Modified

| File | Action |
|------|--------|
| `backend/schemas/enhance.py` | [NEW] Request/response Pydantic models for enhance |
| `backend/schemas/history.py` | [NEW] Response models for history list |
| `backend/schemas/profile.py` | [NEW] Response model for profile |
| `backend/routers/enhance.py` | [NEW] `POST /api/enhance` |
| `backend/routers/history.py` | [NEW] `GET /api/history` |
| `backend/routers/profile.py` | [NEW] `GET /api/profile` |
| `backend/main.py` | [MODIFY] Register all routers |

### Endpoint Specifications

#### `POST /api/enhance`
```
Auth:    Required (Bearer token)
Body:    multipart/form-data — field "file": UploadFile
Returns: 200 { job_id, status, result_url, input_w, input_h, output_w, output_h, processing_time_ms }
Errors:
  401 — Missing or invalid token
  413 — File exceeds MAX_UPLOAD_BYTES (2MB)
  415 — Unsupported file format (not JPEG or PNG)
  422 — No file attached
  500 — SRGAN inference error (logged, sanitized message returned)

Steps:
  1. Auth via get_current_user()
  2. Read file bytes, validate size and format
  3. Create EnhancementJob row (status=pending)
  4. Write input file to uploads/{user_id}/{job_id}.ext
  5. Update job status → processing
  6. Run enhance_image(input_bytes)
  7. Write output to results/{user_id}/{job_id}.png
  8. Update job row → completed with all output metadata
  9. Update user_usage_stats (atomic with job update)
  10. Write audit_log (action="job.completed")
  11. Return response JSON
```

#### `GET /api/history`
```
Auth:    Required
Params:  ?page=1&page_size=10  (default: page=1, page_size=10, max page_size=50)
Returns: 200 { items: [...], total: int, page: int, page_size: int }
Each item: { job_id, status, original_filename, input_w, input_h, output_w, output_h,
             scale_factor, processing_time_ms, created_at, result_url }
Filters: Only completed jobs, deleted_at IS NULL, ordered by created_at DESC
```

#### `GET /api/profile`
```
Auth:    Required
Returns: 200 { uid, email, display_name, photo_url, auth_provider, member_since,
               stats: { total_jobs, successful_jobs, failed_jobs, last_job_at } }
Source:  Single JOIN query on users + user_usage_stats (no COUNT aggregation)
```

#### `GET /api/results/{filename}`
```
Auth:    Required
Params:  filename — the result image filename
Returns: FileResponse (image/png)
Security: Verify the requesting user owns the file (match user_id in path)
Errors:  403 if user doesn't own file, 404 if file doesn't exist
```

### Tests — `tests/test_enhance.py`

```python
# Uses FastAPI TestClient with:
#   - In-memory SQLite test DB
#   - Mocked get_current_user() → returns fake User object
#   - Mocked enhance_image() → returns (fake_png_bytes, fake_metadata_dict)

# Test 1: Valid upload → 200, response contains job_id and result_url
# Test 2: No file attached → 422
# Test 3: File exceeds 2MB → 413
# Test 4: Non-image file (text/plain) → 415
# Test 5: Unauthenticated request (no Bearer header) → 401
# Test 6: After successful enhance, EnhancementJob row status = "completed"
# Test 7: After successful enhance, user_usage_stats.successful_jobs incremented
# Test 8: SRGAN mock raises RuntimeError → job status = "failed", response 500
```

### Tests — `tests/test_history.py`

```python
# Test 1: Empty history → 200, items=[], total=0
# Test 2: 3 completed jobs → 200, items length = 3
# Test 3: Soft-deleted jobs excluded from results
# Test 4: page_size=1, page=2 → correct pagination offset applied
# Test 5: page_size > 50 → clamped to 50
# Test 6: Unauthenticated → 401
```

### Tests — `tests/test_profile.py`

```python
# Test 1: Valid token → 200, all expected fields present
# Test 2: stats.total_jobs reflects actual job count
# Test 3: New user (no jobs) → stats all zeroes, last_job_at null
# Test 4: Unauthenticated → 401
```

### Verification Gateway

```bash
# Run full test suite:
pytest backend/tests/ -v --cov=backend --cov-report=term-missing
# Target: 100% of defined tests PASS, ≥ 80% code coverage

# API smoke test (server running, valid token substituted):
curl -X POST http://localhost:8000/api/enhance \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@tests/fixtures/sample_lr.png"
# → 200 with JSON body

curl http://localhost:8000/api/history \
  -H "Authorization: Bearer $TOKEN"
# → 200 with paginated list

curl http://localhost:8000/api/profile \
  -H "Authorization: Bearer $TOKEN"
# → 200 with user profile + stats
```

### Completion Checklist
- [x] Create `backend/schemas/enhance.py`, `history.py`, `profile.py`
- [x] Implement `POST /api/enhance` (upload, validate, invoke model, save results)
- [x] Implement `GET /api/history` (paginate completed jobs)
- [x] Implement `GET /api/profile` (return user stats)
- [x] Register routers in `main.py`
- [x] Write tests using mock dependencies
- **Status**: COMPLETED - Commit: `662353f` (feat: Implement Milestone 1.5 — API Endpoints)
- `[ ]` Full test suite runs: `pytest backend/tests/ -v` with zero failures
- `[ ]` Code coverage ≥ 80%
- `[ ]` `black` and `isort` pass with no diffs

**Commit**: `feat: Implement Milestone 1.5 — Full API endpoints with auth, validation, DB writes`
**Commit Hash**: `662353f`

---

---

## Phase 1 Completion Gate

> **All of the following must be true before Phase 2 (Frontend) begins:**

- `[ ]` All 5 milestones complete and committed
- `[ ]` Full test suite passes: `pytest backend/tests/ -v` → 0 failures, 0 errors
- `[ ]` Code coverage report: ≥ 80%
- `[ ]` `black backend/` — no formatting violations
- `[ ]` `isort backend/` — no import order violations
- `[ ]` Server starts cleanly: `uvicorn main:app` — no warnings, no errors
- `[ ]` SRGAN model loads on CUDA at startup
- `[ ]` Real end-to-end test: upload a real 128×128 PNG → receive 512×512 SR output
- `[ ]` Repository is clean: no `__pycache__/`, no `.env`, no `*.db`, no `uploads/`, no `results/`
- `[ ]` All 5 milestone commits pushed to GitHub `main`
- `[ ]` README documents exact setup steps (venv, `.env`, model download, run command)

---

## Progress Log

| Milestone | Status | Commit Hash | Date |
|-----------|--------|-------------|------|
| 1.1 — Scaffold & Environment | `[x] Complete` | `92c5f3c` | 2026-08-22 |
| 1.2 — Database Layer | `[x] Complete` | `67322c8` | 2026-08-22 |
| 1.3 — Auth Middleware | `[x] Complete` | `8808b64` | 2026-08-22 |
| 1.4 — SRGAN Inference Service | `[x] Complete` | `6f35025` | 2026-08-22 |
| 1.5 — API Endpoints | `[ ] Pending` | — | — |
| **Phase 1 Complete** | `[ ] Pending` | — | — |
