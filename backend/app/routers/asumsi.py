"""Panel Asumsi (§9.9) — pembeda utama. Mengubah nilai langsung mempengaruhi
seluruh perhitungan di layar lain."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import wajib_peran
from app.database import get_db
from app.models import Konfigurasi, TierKendaraan
from app.models.enums import TipeKonfigurasi
from app.schemas.asumsi import KonfigurasiOut, KonfigurasiPatch, TierKendaraanOut, TierKendaraanPatch

router = APIRouter(tags=["panel-asumsi"])


def _validasi_nilai(nilai: str, tipe: TipeKonfigurasi) -> None:
    try:
        if tipe == TipeKonfigurasi.INT:
            int(nilai)
        elif tipe == TipeKonfigurasi.FLOAT:
            float(nilai)
        elif tipe == TipeKonfigurasi.BOOL:
            if nilai.strip().lower() not in ("true", "false", "1", "0", "ya", "yes", "no", "on", "off"):
                raise ValueError
        # STRING selalu valid
    except ValueError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"Nilai '{nilai}' tidak sesuai tipe {tipe.value}"
        )


@router.get("/konfigurasi", response_model=list[KonfigurasiOut])
def daftar_konfigurasi(pengguna=Depends(wajib_peran("PETUGAS")), db: Session = Depends(get_db)):
    return db.query(Konfigurasi).order_by(Konfigurasi.kunci).all()


@router.patch("/konfigurasi/{kunci}", response_model=KonfigurasiOut)
def ubah_konfigurasi(
    kunci: str, body: KonfigurasiPatch, pengguna=Depends(wajib_peran("PETUGAS")), db: Session = Depends(get_db)
):
    konf = db.get(Konfigurasi, kunci)
    if konf is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kunci konfigurasi tidak ditemukan")
    _validasi_nilai(body.nilai, konf.tipe)
    konf.nilai = body.nilai
    db.commit()
    db.refresh(konf)
    return konf


@router.get("/tier-kendaraan", response_model=list[TierKendaraanOut])
def daftar_tier(pengguna=Depends(wajib_peran("PETUGAS")), db: Session = Depends(get_db)):
    return db.query(TierKendaraan).order_by(TierKendaraan.urutan).all()


@router.patch("/tier-kendaraan/{tier_id}", response_model=TierKendaraanOut)
def ubah_tier(
    tier_id: UUID, body: TierKendaraanPatch, pengguna=Depends(wajib_peran("PETUGAS")), db: Session = Depends(get_db)
):
    tier = db.get(TierKendaraan, tier_id)
    if tier is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tier kendaraan tidak ditemukan")
    perubahan = body.model_dump(exclude_unset=True)
    for field in ("kapasitas_kg", "tarif_dasar", "tarif_per_km"):
        if field in perubahan and perubahan[field] is not None and perubahan[field] <= 0:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"{field} harus > 0")
    for field, nilai in perubahan.items():
        if nilai is not None:
            setattr(tier, field, nilai)
    db.commit()
    db.refresh(tier)
    return tier
