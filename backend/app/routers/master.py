from fastapi import APIRouter, Depends

from app.auth import get_pengguna_aktif
from app.routers import stub_fase_0
from app.schemas.master import KomoditasOut, KoperasiOut, PenerimaOut

router = APIRouter(tags=["master"])


@router.get("/komoditas", response_model=list[KomoditasOut])
def daftar_komoditas(pengguna=Depends(get_pengguna_aktif)):
    stub_fase_0()


@router.get("/penerima", response_model=list[PenerimaOut])
def daftar_penerima(pengguna=Depends(get_pengguna_aktif)):
    stub_fase_0()


@router.get("/koperasi/saya", response_model=KoperasiOut)
def koperasi_saya(pengguna=Depends(get_pengguna_aktif)):
    """Koperasi milik pengguna login (gudang = titik awal rute)."""
    stub_fase_0()
