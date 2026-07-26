"""Endpoint Berita Acara (§9.8) — FE merender halaman cetak window.print()."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.auth import get_pengguna_aktif
from app.routers import stub_fase_0
from app.schemas.berita import BeritaAcaraOut

router = APIRouter(tags=["berita-acara"])


@router.get("/slot/{slot_id}/berita-acara", response_model=BeritaAcaraOut)
def berita_acara(slot_id: UUID, pengguna=Depends(get_pengguna_aktif)):
    """Agregat: lot + foto muat & bongkar, keputusan, atribusi, rincian ongkos
    per petani, subsidi koperasi. Tanda tangan = garis kosong cetak (K4)."""
    stub_fase_0()
