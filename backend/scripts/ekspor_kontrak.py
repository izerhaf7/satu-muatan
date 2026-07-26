"""Ekspor artefak kontrak (dijalankan arsitek, Fase 0 / saat kontrak berubah):

- kontrak/openapi.yaml  ← app.openapi() (sumber kebenaran bentuk API)
- kontrak/skema.sql     ← DDL dari metadata SQLAlchemy (referensi bacaan;
                          sumber kebenaran skema = migrasi Alembic)

Jalankan dari folder backend:  python scripts/ekspor_kontrak.py
"""

import pathlib
import sys

import yaml
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.database import Base  # noqa: E402
from app import models as _models  # noqa: E402,F401  (registrasi seluruh tabel)
from app.main import app  # noqa: E402

KONTRAK = pathlib.Path(__file__).resolve().parents[2] / "kontrak"
KONTRAK.mkdir(exist_ok=True)


def ekspor_openapi() -> None:
    skema = app.openapi()
    tujuan = KONTRAK / "openapi.yaml"
    tujuan.write_text(yaml.safe_dump(skema, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"OK  {tujuan} ({len(skema['paths'])} path)")


def ekspor_skema_sql() -> None:
    baris = [
        "-- REFERENSI BACAAN. Sumber kebenaran skema = migrasi Alembic (backend/alembic/).",
        "-- Digenerate dari metadata SQLAlchemy oleh scripts/ekspor_kontrak.py.",
        "",
    ]
    for tabel in Base.metadata.sorted_tables:
        ddl = str(CreateTable(tabel).compile(dialect=postgresql.dialect()))
        baris.append(ddl.strip() + ";")
        baris.append("")
    tujuan = KONTRAK / "skema.sql"
    tujuan.write_text("\n".join(baris), encoding="utf-8")
    print(f"OK  {tujuan} ({len(Base.metadata.sorted_tables)} tabel)")


if __name__ == "__main__":
    ekspor_openapi()
    ekspor_skema_sql()
