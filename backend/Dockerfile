# syntax=docker/dockerfile:1
# Backend produksi (spec §3.3): Render/Railway menjalankan image ini langsung.
# Postgres TIDAK ada di sini — Docker Compose untuk produksi dilarang (spec §12);
# DATABASE_URL menunjuk ke Postgres terkelola (Neon/Supabase) lewat env platform.
FROM python:3.12-slim

WORKDIR /app

# psycopg[binary] (requirements.txt) sudah membawa libpq statis — tidak perlu
# build-essential/libpq-dev, image tetap kecil.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# Layer dependensi terpisah dari layer kode -- cache pip install selama
# requirements.txt tidak berubah (spec §3.1 tidak melarang, ini murni build cache).
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x docker-entrypoint.sh \
    && useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Koefisien BISNIS tidak pernah lewat env (aturan keras CLAUDE.md #1) -- hanya
# konfigurasi TEKNIS (DATABASE_URL, JWT_SECRET, VENDOR_ADAPTER, DEMO_MODE,
# CORS_ORIGINS) disuntik platform saat deploy. Lihat backend/.env.example.
# Tidak ada rahasia di dalam image ini.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT','8000') + '/healthz', timeout=3)" || exit 1

# Migrasi aktif secara default agar Render/Railway tetap sama. Cloud Run menyetel
# RUN_MIGRATIONS=false lalu memakai migration job terpisah sebelum rollout.
ENTRYPOINT ["./docker-entrypoint.sh"]
