# ---- Build stage: compilers live here only ----------------------------------
FROM python:3.11-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
COPY requirements.txt .

# basicsr's setup.py needs torch/numpy/Cython already installed at build time,
# but requirements.txt is alphabetical (basicsr comes before torch). Install the
# build prerequisites first, using the pins from requirements.txt, so basicsr
# does not try to fetch them itself (which is slow and fails).
# --no-build-isolation also avoids memory errors building torchvision/basicsr.
RUN grep -E '^(--extra-index-url|torch==|torchvision==|numpy==|Cython==)' requirements.txt > build-prereqs.txt \
    && pip install -r build-prereqs.txt \
    && pip install --no-build-isolation -r requirements.txt

# ---- Runtime stage: no compilers, runs as an unprivileged user ----------------
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:$PATH" \
    HOME=/home/app

# libgl1 + libglib2.0-0: shared libraries OpenCV loads at import (libgl1 brings
# in libxcb; without it `import cv2` fails even for the headless build).
# gosu: start.sh drops from root to the app user.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    gosu \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --uid 10001 --create-home --home-dir /home/app app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Bake the model weights into the image (they are not in git). Done before the
# application code is copied so this large layer is cached across code changes.
COPY scripts/download_weights.py scripts/download_weights.py
RUN python scripts/download_weights.py

COPY . .
RUN chown app:app /app && chmod +x start.sh

# Expose the application port
EXPOSE 8000

# Liveness probe (Railway uses /ready via the service healthcheck setting)
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','8000'))" || exit 1

# start.sh starts as root only to fix volume ownership, then runs as `app`.
# It applies migrations, then starts uvicorn on $PORT (default 8000).
CMD ["./start.sh"]
