from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_pengguna_aktif
from app.database import get_db
from app.models import Komoditas, Koperasi, Penerima
from app.schemas.master import KomoditasOut, KoperasiOut, PenerimaOut

router = APIRouter(tags=["master"])


@router.get("/komoditas", response_model=list[KomoditasOut])
def daftar_komoditas(pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    return db.query(Komoditas).order_by(Komoditas.nama).all()


@router.get("/penerima", response_model=list[PenerimaOut])
def daftar_penerima(pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    return db.query(Penerima).order_by(Penerima.nama).all()


@router.get("/koperasi/saya", response_model=KoperasiOut)
def koperasi_saya(pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    """Koperasi milik pengguna login (gudang = titik awal rute)."""
    if pengguna.koperasi_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pengguna ini tidak terhubung ke koperasi")
    koperasi = db.get(Koperasi, pengguna.koperasi_id)
    if koperasi is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Koperasi tidak ditemukan")
    return koperasi
