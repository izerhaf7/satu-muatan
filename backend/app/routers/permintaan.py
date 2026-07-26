from fastapi import APIRouter, Depends

from app.auth import get_pengguna_aktif, wajib_peran
from app.routers import stub_fase_0
from app.schemas.permintaan import PermintaanCreate, PermintaanOut

router = APIRouter(prefix="/permintaan", tags=["permintaan"])


@router.get("", response_model=list[PermintaanOut])
def daftar_permintaan(pengguna=Depends(get_pengguna_aktif)):
    """Ter-scope per peran (K6): PENERIMA → miliknya; KOPERASI → semua yang terbuka."""
    stub_fase_0()


@router.post("", response_model=PermintaanOut, status_code=201)
def buat_permintaan(body: PermintaanCreate, pengguna=Depends(wajib_peran("PENERIMA"))):
    stub_fase_0()
