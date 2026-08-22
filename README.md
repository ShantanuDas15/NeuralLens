# NeuralLens

> AI-Powered Image Super-Resolution Web Application — Backend API

---

## Requirements

- Python 3.11+ (3.14 confirmed working)
- NVIDIA GPU with CUDA 12.4+ (RTX 4060 Laptop GPU recommended)
- Git

---

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd NeuralLens
```

### 2. Create and activate the virtual environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 3. Install production dependencies

```bash
pip install --upgrade pip

# PyTorch with CUDA 12.4 (must be installed separately)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# All other production dependencies
pip install -r requirements.txt
```

### 4. Install development / test dependencies

```bash
pip install -r requirements-dev.txt
```

### 5. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in your Firebase credentials and settings
```

### 6. Add Firebase service account

- Download your Firebase service account JSON from the Firebase Console.
- Place it at the path specified in `FIREBASE_SERVICE_ACCOUNT_PATH` (default: `./firebase-service-account.json`).
- **Never commit this file.**

### 7. Download Real-ESRGAN model weights

```bash
mkdir -p weights
wget -O weights/RealESRGAN_x4plus.pth \
  "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
```

---

## Running the Backend

```bash
# From backend/ with venv active:
uvicorn main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## Running Tests

```bash
# From backend/ with venv active:
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## Code Quality

```bash
black .
isort .
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | FastAPI + Uvicorn |
| ML Inference | PyTorch + Real-ESRGAN |
| Image Processing | OpenCV + Pillow |
| Database | SQLite (dev) → PostgreSQL (prod) via SQLAlchemy |
| Authentication | Firebase Admin SDK |
| Validation | Pydantic v2 |
