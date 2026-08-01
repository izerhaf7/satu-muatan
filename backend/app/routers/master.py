from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_pengguna_aktif
from app.database import get_db
from app.models import Komoditas, Penerima, TitikKumpul
from app.schemas.master import KomoditasOut, PenerimaOut, TitikKumpulOut

router = APIRouter(tags=["master"])


@router.get("/komoditas", response_model=list[KomoditasOut])
def daftar_komoditas(pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    return db.query(Komoditas).order_by(Komoditas.nama).all()


@router.get("/penerima", response_model=list[PenerimaOut])
def daftar_penerima(pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    return db.query(Penerima).order_by(Penerima.nama).all()


@router.get("/titik-kumpul/saya", response_model=TitikKumpulOut)
def titik_kumpul_saya(pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    """Titik kumpul milik pengguna login (titik awal rute). Rename v2 §2: dulu /koperasi/saya."""
    if pengguna.titik_kumpul_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pengguna ini tidak terhubung ke titik kumpul")
    titik_kumpul = db.get(TitikKumpul, pengguna.titik_kumpul_id)
    if titik_kumpul is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Titik kumpul tidak ditemukan")
    return titik_kumpul
