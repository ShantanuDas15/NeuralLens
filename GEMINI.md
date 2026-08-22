# NeuralLens — Agent Rulebook & Permanent Memory

> This file is the single source of truth for every Antigravity AI session working in this repository.
> All rules defined here are **mandatory and non-negotiable** and override any general default agent behaviour.

---

## 1. Project Context

**Project**: NeuralLens — AI-Powered Image Super-Resolution Web Application
**Domain**: Computer Vision · Generative AI · Full-Stack Web Development
**Stack**: React 18 + Vite (Frontend) · FastAPI + PyTorch + Python 3.11 (Backend) · Firebase Auth · SQLite → PostgreSQL · SQLAlchemy

**Key Reference Documents** (read before planning any implementation):
- `PROJECT.md` — Full project description, features, and tech stack
- `DATABASE_DESIGN.md` — Production-grade database schema, table definitions, ER diagram, index strategy

---

## 2. Development Order — MANDATORY

> **THE BACKEND MUST BE FULLY IMPLEMENTED, VALIDATED, TESTED, AND HARDENED BEFORE ANY FRONTEND WORK BEGINS.**

This is a hard rule. No React component, no frontend route, no UI code is to be written until:
1. All backend API endpoints are implemented and passing tests.
2. The database schema is migrated and verified.
3. Firebase Admin SDK token verification is confirmed working.
4. The SRGAN/Real-ESRGAN inference pipeline is tested end-to-end.
5. All backend tests pass cleanly with zero errors.

If asked to implement a frontend feature before the backend is complete and validated — **decline and redirect** to the pending backend milestone.

---

## 3. Core Implementation Workflow

Whenever any feature, milestone, or sub-task from any phase plan is executed, YOU MUST follow this exact sequence without exception:

### Step 1 — Implement
- Write code strictly as specified in the milestone or phase plan documentation.
- Follow the project's established directory structure (`backend/routers/`, `backend/services/`, `backend/models/`, etc.).
- Do not introduce new dependencies without updating `requirements.txt`.
- Never hardcode secrets, credentials, or file paths — use `.env` and `python-dotenv`.

### Step 2 — Verify, Validate & Test
- Execute the **Verification Gateway** or test instructions specified in the phase plan for that milestone.
- If no test instructions exist in the plan, YOU MUST ask for permission before generating new test cases.
- Run all tests via the terminal. Do **not** assume tests pass — confirm with actual command output.
- Tests must cover: happy path, error cases, edge cases, and security boundary conditions (e.g. unauthenticated requests, oversized inputs).

### Step 3 — Clean & Isolate
Before any `git` operation, scrub the repository of:
- `__pycache__/` directories anywhere in the tree
- `.pytest_cache/` outside of `backend/`
- `*.pyc` compiled Python files
- `.DS_Store` files (macOS artefacts)
- Temporary test scripts or dummy data files
- Any `.env` file (must never be committed)

Verify `.gitignore` is correctly catching all of the above.

### Step 4 — Commit & Push
- **ONLY** commit if all tests pass and the directory is clean.
- Use the following commit message format:
  ```
  feat: Implement Milestone X.X — <short description>
  
  <Optional body: key decisions, what was tested, known limitations>
  ```
- Push to the GitHub remote after every successful milestone commit.

### Step 5 — Track Progress
- After a successful commit, update the relevant phase plan markdown file (e.g. `PHASE_1_BACKEND_PLAN.md`) by:
  - Checking off completed tasks (`[ ]` → `[x]`)
  - Appending the exact commit hash to the milestone's status log entry

---

## 4. Phase Plan Generation & Test Design Standards

When generating, drafting, or updating any Phase Development Plan or milestone specification, YOU MUST adhere to all of the following:

### 4.1 Structured & Professional Test Design
Every milestone MUST include explicitly defined test specifications covering:
- **Unit tests**: Individual functions and service methods in isolation
- **Integration tests**: API endpoint behaviour with a real (in-memory) database
- **Boundary condition checks**: Edge inputs (empty files, max size, wrong format, expired tokens)
- **API Verification Gateways**: `curl` or `pytest` commands that confirm the endpoint returns the exact expected status code and response shape

### 4.2 Deployment Safety & Zero Error Guarantee
- Tests MUST NOT call live external services (Firebase, real SRGAN inference on large images in CI).
- Use **mocks and stubs** for: Firebase Admin SDK token verification, SRGAN model inference, filesystem I/O.
- Tests must be deterministic — the same test run must always produce the same result.
- No test should leave residual state (DB rows, temp files) that affects subsequent test runs.

### 4.3 Fixture Scrubbing & Environment Isolation
- All test fixtures (temp DB, temp uploaded files, mock result images) must be torn down automatically in `teardown` / `pytest` fixtures.
- Use a **separate SQLite test database** (e.g. `neurallens_test.db` or in-memory `sqlite://`) — never run tests against the development or production database.
- Mock Firebase tokens must be hardcoded test values, never real user credentials.

---

## 5. Backend Architecture Reference

```
backend/
├── main.py                    # FastAPI app, lifespan, CORS, router registration
├── routers/
│   ├── enhance.py             # POST /api/enhance
│   ├── history.py             # GET  /api/history
│   └── profile.py             # GET  /api/profile
├── services/
│   ├── srgan.py               # Real-ESRGAN model singleton + inference
│   └── image_utils.py         # OpenCV/Pillow preprocessing & postprocessing
├── models/
│   └── database.py            # SQLAlchemy ORM models (User, EnhancementJob, etc.)
├── middleware/
│   └── auth.py                # Firebase Admin SDK token verification dependency
├── db/
│   └── session.py             # SQLAlchemy engine + session factory
├── weights/
│   └── RealESRGAN_x4plus.pth  # Pre-trained model weights (gitignored if >100MB)
├── uploads/                   # LR input images stored by user_id/job_id (gitignored)
├── results/                   # SR output images stored by user_id/job_id (gitignored)
├── tests/
│   ├── conftest.py            # Shared fixtures: test DB, mock auth, mock SRGAN
│   ├── test_enhance.py
│   ├── test_history.py
│   ├── test_profile.py
│   └── test_auth.py
├── requirements.txt
└── .env                       # Never committed — contains Firebase credentials, DB URL
```

---

## 6. Database Schema Reference

Five production-grade tables. Full specification in `DATABASE_DESIGN.md`.

| Table | Purpose |
|-------|---------|
| `users` | Local projection of Firebase Auth user. Created on first authenticated API call |
| `model_configs` | Registry of available SR models. Seeded at migration time |
| `enhancement_jobs` | One row per enhancement request. Full lifecycle tracking |
| `user_usage_stats` | Pre-aggregated per-user counters. Avoids `COUNT(*)` on profile load |
| `audit_logs` | Append-only security & event log. Never updated, never deleted |

**Critical schema rules**:
- All PKs are `UUID` strings — never serial integers
- All tables use `created_at` + `updated_at` audit timestamps
- `users` and `enhancement_jobs` use `deleted_at` for soft deletes — never hard-delete rows
- `enhancement_jobs.meta` is a JSON column for Phase 2 extensibility without migrations

---

## 7. API Endpoint Contracts

| Method | Path | Auth Required | Description |
|--------|------|:---:|-------------|
| `POST` | `/api/enhance` | ✅ | Upload LR image → returns SR image URL + job metadata |
| `GET` | `/api/history` | ✅ | Paginated list of user's completed enhancement jobs |
| `GET` | `/api/profile` | ✅ | User profile + pre-aggregated usage stats |
| `GET` | `/api/results/{filename}` | ✅ | Serve SR result image file |
| `GET` | `/health` | ❌ | Liveness check — returns `{ "status": "ok" }` |

All protected endpoints validate the `Authorization: Bearer <Firebase ID Token>` header via `middleware/auth.py`.

---

## 8. Environment & Security Rules

- **Never commit `.env`** — it must be in `.gitignore` before the first commit.
- Secrets stored in `.env`: `FIREBASE_PROJECT_ID`, `FIREBASE_SERVICE_ACCOUNT_PATH`, `DATABASE_URL`, `UPLOAD_DIR`, `RESULTS_DIR`, `MAX_UPLOAD_BYTES`.
- `firebase-service-account.json` must be **gitignored** — it contains private GCP credentials.
- The `uploads/` and `results/` directories must be gitignored — they contain user data.
- The `weights/` directory: if the `.pth` file exceeds 100MB, use Git LFS or document manual download steps in the README. Do not force-push large binaries.

---

## 9. Coding Standards

- **Python style**: PEP 8. Use `black` for formatting, `isort` for import ordering.
- **Type hints**: All function signatures must use Python type hints.
- **Docstrings**: All service methods and router handlers must have a one-line docstring.
- **Error handling**: Never let unhandled exceptions propagate to the client. Use FastAPI `HTTPException` with appropriate status codes.
- **Logging**: Use Python's `logging` module (not `print`). Log at `INFO` for normal flow, `ERROR` for exceptions.
- **No global mutable state** except the SRGAN model singleton (loaded once at lifespan startup).

---

## 10. Git & Repository Hygiene

- **Branch strategy**: `main` is the stable branch. Feature work on `feat/<milestone-name>` branches. Merge only after tests pass.
- **`.gitignore` must include**: `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.DS_Store`, `.env`, `firebase-service-account.json`, `uploads/`, `results/`, `*.db`, `neurallens_test.db`.
- **Commit atomically**: One commit per completed milestone — not per file save.
- **Never force-push** to `main`.
