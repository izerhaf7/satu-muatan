#!/bin/sh
# Entrypoint produksi: Render/Railway mempertahankan migrasi saat start secara
# default. Cloud Run menonaktifkannya dan menjalankan migrasi satu kali lewat job
# terpisah sebelum revision tanpa traffic dibuat. $PORT disuntik platform;
# default 8000 untuk `docker run` lokal.
set -e

if [ "${RUN_MIGRATIONS:-true}" = "false" ]; then
    echo "[entrypoint] alembic dilewati (RUN_MIGRATIONS=${RUN_MIGRATIONS})"
else
    echo "[entrypoint] alembic upgrade head..."
    alembic upgrade head
fi

echo "[entrypoint] uvicorn di port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
