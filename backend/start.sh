#!/bin/sh
# Container entrypoint: fix data-dir ownership, apply DB migrations, start the API.
set -e

# Railway mounts volumes root-owned at runtime, after the image is built, so an
# unprivileged user could not write uploads to them. Start as root, give the
# app user the data directories, then re-run this script as that user.
if [ "$(id -u)" = "0" ]; then
  app_uid="$(id -u app)"
  for dir in "${UPLOAD_DIR:-uploads}" "${RESULTS_DIR:-results}"; do
    mkdir -p "$dir"
    # Only walk the tree when the top level is wrong (cheap on every later boot).
    if [ "$(stat -c %u "$dir")" != "$app_uid" ]; then
      chown -R app:app "$dir"
    fi
  done
  exec gosu app "$0" "$@"
fi

echo "Running database migrations..."
alembic upgrade head

echo "Starting NeuralLens API on port ${PORT:-8000}..."
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1 --timeout-graceful-shutdown 30
