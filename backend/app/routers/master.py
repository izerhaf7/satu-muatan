from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_pengguna_aktif
from app.database import get_db
from app.models import Komoditas, Penerima, TitikKumpul
from app.schemas.master import AturanKirimanOut, KomoditasOut, PenerimaOut, TitikKumpulOut
from app.services.konfigurasi import baca_konfigurasi

router = APIRouter(tags=["master"])


@router.get("/aturan-kiriman", response_model=AturanKirimanOut)
def aturan_kiriman(pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    """K14: ambang kiriman untuk divalidasi di layar Kirim Panen — supaya petani
    tahu batasnya SEBELUM menekan tombol, bukan lewat galat 422 sesudahnya."""
    return AturanKirimanOut(
        volume_minimal_kg=baca_konfigurasi(db, "volume_minimal_kg"),
        jarak_maks_layanan_km=baca_konfigurasi(db, "jarak_maks_layanan_km"),
    )


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
