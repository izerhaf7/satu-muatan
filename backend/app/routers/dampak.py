"""Endpoint Dashboard Dampak (§9.10) + sumber 'Ringkasan bulan ini' Beranda (§9.2)."""

from fastapi import APIRouter, Depends

from app.auth import get_pengguna_aktif
from app.routers import stub_fase_0
from app.schemas.dampak import DampakBulananOut, DampakRingkasanOut

router = APIRouter(prefix="/dampak", tags=["dampak"])


@router.get("/ringkasan", response_model=DampakRingkasanOut)
def dampak_ringkasan(pengguna=Depends(get_pengguna_aktif)):
    """4 kartu, masing-masing dengan rumus + status_sumber. Tanpa data = null → '—'."""
    stub_fase_0()


@router.get("/bulanan", response_model=list[DampakBulananOut])
def dampak_bulanan(pengguna=Depends(get_pengguna_aktif)):
    """Grafik batang per bulan (Recharts) — termasuk jumlah_kiriman (K6)."""
    stub_fase_0()
