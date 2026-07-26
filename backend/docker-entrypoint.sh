#!/bin/sh
# Entrypoint produksi (spec §3.3): migrasi dulu, baru nyalakan API — supaya skema
# selalu sinkron dengan kode sebelum menerima trafik. $PORT disuntik platform
# (Render/Railway); default 8000 untuk `docker run` lokal.
set -e

echo "[entrypoint] alembic upgrade head..."
alembic upgrade head

echo "[entrypoint] uvicorn di port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
