#!/bin/sh
# Container entrypoint: apply DB migrations, then start the API.
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting NeuralLens API on port ${PORT:-8000}..."
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
