"""Panel Asumsi (§9.9) — pembeda utama. Mengubah nilai langsung mempengaruhi
seluruh perhitungan di layar lain."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.auth import wajib_peran
from app.routers import stub_fase_0
from app.schemas.asumsi import KonfigurasiOut, KonfigurasiPatch, TierKendaraanOut, TierKendaraanPatch

router = APIRouter(tags=["panel-asumsi"])


@router.get("/konfigurasi", response_model=list[KonfigurasiOut])
def daftar_konfigurasi(pengguna=Depends(wajib_peran("KOPERASI"))):
    stub_fase_0()


@router.patch("/konfigurasi/{kunci}", response_model=KonfigurasiOut)
def ubah_konfigurasi(kunci: str, body: KonfigurasiPatch, pengguna=Depends(wajib_peran("KOPERASI"))):
    stub_fase_0()


@router.get("/tier-kendaraan", response_model=list[TierKendaraanOut])
def daftar_tier(pengguna=Depends(wajib_peran("KOPERASI"))):
    stub_fase_0()


@router.patch("/tier-kendaraan/{tier_id}", response_model=TierKendaraanOut)
def ubah_tier(tier_id: UUID, body: TierKendaraanPatch, pengguna=Depends(wajib_peran("KOPERASI"))):
    stub_fase_0()
