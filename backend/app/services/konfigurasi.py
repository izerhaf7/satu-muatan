"""Baca koefisien bisnis dari tabel `konfigurasi` / `tier_kendaraan` (CLAUDE.md aturan #1).

Tidak ada satu pun angka bisnis boleh hardcode di router/services — semua lewat
`baca_konfigurasi()` / `baca_tiers_aktif()` di modul ini.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.domain.armada import Tier
from app.models import Konfigurasi, TierKendaraan
from app.models.enums import TipeKonfigurasi


def _cast(nilai: str, tipe: TipeKonfigurasi) -> Any:
    if tipe == TipeKonfigurasi.INT:
        return int(nilai)
    if tipe == TipeKonfigurasi.FLOAT:
        return float(nilai)
    if tipe == TipeKonfigurasi.BOOL:
        return nilai.strip().lower() in ("true", "1", "ya", "yes", "on")
    return nilai  # STRING


def baca_konfigurasi(db: Session, kunci: str) -> Any:
    """Ambil satu nilai konfigurasi, di-cast sesuai kolom `tipe`."""
    baris = db.get(Konfigurasi, kunci)
    if baris is None:
        raise KeyError(f"konfigurasi '{kunci}' tidak ditemukan — jalankan seed/seed.py")
    return _cast(baris.nilai, baris.tipe)


def baca_semua_konfigurasi(db: Session) -> dict[str, Any]:
    return {baris.kunci: _cast(baris.nilai, baris.tipe) for baris in db.query(Konfigurasi).all()}


def baca_tiers_aktif(db: Session) -> list[Tier]:
    """Tier kendaraan aktif, terurut sesuai kolom `urutan` (dipakai mesin harga/armada)."""
    baris = db.query(TierKendaraan).filter_by(aktif=True).order_by(TierKendaraan.urutan).all()
    return [
        Tier(kode=t.kode, kapasitas_kg=t.kapasitas_kg, tarif_dasar=t.tarif_dasar, tarif_per_km=t.tarif_per_km)
        for t in baris
    ]
