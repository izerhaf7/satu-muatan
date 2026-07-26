"""Riwayat partisipasi petani (layar Riwayat, §2.5)."""

from fastapi import APIRouter, Depends

from app.auth import wajib_peran
from app.routers import stub_fase_0
from app.schemas.riwayat import PartisipasiRiwayatOut

router = APIRouter(tags=["riwayat"])


@router.get("/partisipasi/saya", response_model=list[PartisipasiRiwayatOut])
def partisipasi_saya(pengguna=Depends(wajib_peran("PETANI"))):
    """Riwayat ikut kirim + kembalian milik petani login."""
    stub_fase_0()
