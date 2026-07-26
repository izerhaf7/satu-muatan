"""Fixture bersama test API (Fase 1) — DB test terpisah dari DB dev.

Env DATABASE_URL di-set di level MODUL (sebelum modul `app` manapun diimpor) karena
`app.config.get_settings()` memakai `@lru_cache` — begitu ke-cache dengan URL dev,
tidak bisa diganti lagi dalam proses yang sama.
"""

import os
import pathlib
import sys
from decimal import Decimal

import pytest

# "127.0.0.1", bukan "localhost": di sandbox Windows dev ini resolusi "localhost"
# mencoba IPv6 (::1) dulu terhadap port yang di-forward Docker, menambah ~130 detik
# delay per koneksi baru sebelum jatuh ke IPv4. Sama persis dengan DB yang sudah
# dibuat (postgresql:5433/satu_muatan_test) — cuma bentuk host yang beda.
os.environ["DATABASE_URL"] = "postgresql+psycopg://satu_muatan:satu_muatan_dev@127.0.0.1:5433/satu_muatan_test"
os.environ.setdefault("JWT_SECRET", "rahasia-test-jangan-dipakai-produksi")
os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("VENDOR_ADAPTER", "MOCK")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

PIN_DEMO = "123456"

_SEMUA_TABEL = [
    "serah_terima",
    "jejak_posisi",
    "lot",
    "pengiriman",
    "partisipasi",
    "slot_tujuan",
    "permintaan",
    "slot",
    "pengguna",
    "tier_kendaraan",
    "konfigurasi",
    "komoditas",
    "penerima",
    "koperasi",
]


@pytest.fixture(scope="session", autouse=True)
def _migrasi_database():
    """`alembic upgrade head` terhadap DB test, sekali per sesi pytest — dijalankan
    IN-PROCESS lewat API Python Alembic (bukan subprocess CLI): memanggil `alembic`
    sebagai child process dari dalam proses pytest yang sudah di-background kadang
    macet tanpa error di lingkungan sandbox ini, jadi dihindari sama sekali.

    Skema dikosongkan lewat `DROP SCHEMA public CASCADE` (bukan `alembic downgrade
    base`): migrasi Fase 0 (`backend/alembic/versions/..._skema_awal_14_tabel.py`,
    di luar scope agent ini) hanya `op.drop_table(...)` di downgrade() — tidak
    men-drop TYPE enum Postgres yang menyertainya — sehingga downgrade+upgrade
    berulang gagal dengan `DuplicateObject: type "..." already exists`. Reset
    skema total menghindari itu tanpa perlu menyentuh berkas migrasi.
    """
    import psycopg
    from alembic import command
    from alembic.config import Config

    admin_url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(admin_url, autocommit=True) as conn, conn.cursor() as cur:
        cur.execute("DROP SCHEMA public CASCADE")
        cur.execute("CREATE SCHEMA public")

    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def _bersihkan_tabel(_migrasi_database):
    """Kosongkan seluruh tabel sebelum tiap test — isolasi tanpa perlu trik transaksi."""
    from sqlalchemy import text

    from app.database import engine

    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {', '.join(_SEMUA_TABEL)} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture()
def db():
    from app.database import SessionLocal

    sesi = SessionLocal()
    try:
        yield sesi
    finally:
        sesi.close()


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def data_dasar(db):
    """Konfigurasi + tier (dari seed/seed.py, tidak diubah) + master data minimal
    (koperasi, penerima, komoditas) + 6 akun demo K9 untuk test API.

    Seed penuh (riwayat 8 slot dst.) adalah tugas agent infra-demo di Fase 3 — di
    sini kita hanya butuh cukup data supaya endpoint API bisa diuji end-to-end.
    """
    from seed.seed import seed_konfigurasi, seed_tier

    from app.auth import hash_pin
    from app.models import Komoditas, Koperasi, Penerima, Pengguna
    from app.models.enums import PeranPengguna, StatusSumber, TipePenerima

    seed_tier(db)
    seed_konfigurasi(db)
    db.commit()

    koperasi = Koperasi(
        nama="Koperasi Desa Mekarjaya",
        kode="CKJ",
        desa="Cikajang",
        kecamatan="Cikajang",
        kabupaten="Garut",
        alamat_gudang="Jl. Raya Cikajang",
        lat=-7.3661,
        lng=107.7961,
    )
    db.add(koperasi)
    db.flush()

    penerima_cibiru = Penerima(
        nama="SPPG Cibiru 3", tipe=TipePenerima.SPPG, alamat="Cibiru, Bandung", lat=-6.9269, lng=107.7189
    )
    penerima_ujungberung = Penerima(
        nama="SPPG Ujungberung 1", tipe=TipePenerima.SPPG, alamat="Ujungberung, Bandung", lat=-6.9147, lng=107.7000
    )
    penerima_panyileukan = Penerima(
        nama="SPPG Panyileukan 2", tipe=TipePenerima.SPPG, alamat="Panyileukan, Bandung", lat=-6.9333, lng=107.6989
    )
    db.add_all([penerima_cibiru, penerima_ujungberung, penerima_panyileukan])
    db.flush()

    kubis = Komoditas(
        nama="Kubis",
        satuan="kg",
        harga_acuan_per_kg=3000,
        umur_simpan_jam=168,
        laju_susut_per_jam=Decimal("0.00250"),
        status_sumber=StatusSumber.ASUMSI,
    )
    tomat = Komoditas(
        nama="Tomat",
        satuan="kg",
        harga_acuan_per_kg=5000,
        umur_simpan_jam=96,
        laju_susut_per_jam=Decimal("0.00520"),
        status_sumber=StatusSumber.ASUMSI,
    )
    db.add_all([kubis, tomat])
    db.flush()

    pin_hash = hash_pin(PIN_DEMO)
    akun = {
        "koperasi": Pengguna(
            nama="Bu Nia", no_hp="081200000001", pin_hash=pin_hash, peran=PeranPengguna.KOPERASI, koperasi_id=koperasi.id
        ),
        "asep": Pengguna(
            nama="Asep", no_hp="081200000011", pin_hash=pin_hash, peran=PeranPengguna.PETANI, koperasi_id=koperasi.id
        ),
        "wati": Pengguna(
            nama="Wati", no_hp="081200000012", pin_hash=pin_hash, peran=PeranPengguna.PETANI, koperasi_id=koperasi.id
        ),
        "dedi": Pengguna(
            nama="Dedi", no_hp="081200000013", pin_hash=pin_hash, peran=PeranPengguna.PETANI, koperasi_id=koperasi.id
        ),
        "ijah": Pengguna(
            nama="Ijah", no_hp="081200000014", pin_hash=pin_hash, peran=PeranPengguna.PETANI, koperasi_id=koperasi.id
        ),
        "penerima_cibiru": Pengguna(
            nama="Bu Rina",
            no_hp="081200000021",
            pin_hash=pin_hash,
            peran=PeranPengguna.PENERIMA,
            penerima_id=penerima_cibiru.id,
        ),
    }
    db.add_all(akun.values())
    db.commit()
    for p in akun.values():
        db.refresh(p)

    return {
        "koperasi": koperasi,
        "penerima": {"cibiru": penerima_cibiru, "ujungberung": penerima_ujungberung, "panyileukan": penerima_panyileukan},
        "komoditas": {"kubis": kubis, "tomat": tomat},
        "pengguna": akun,
    }


@pytest.fixture()
def masuk(client):
    """Fixture callable: masuk(no_hp) -> header Authorization siap pakai."""

    def _masuk(no_hp: str, pin: str = PIN_DEMO) -> dict:
        r = client.post("/api/auth/masuk", json={"no_hp": no_hp, "pin": pin})
        assert r.status_code == 200, r.text
        token = r.json()["token"]
        return {"Authorization": f"Bearer {token}"}

    return _masuk
