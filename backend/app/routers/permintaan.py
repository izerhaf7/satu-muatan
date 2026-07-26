from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_pengguna_aktif, wajib_peran
from app.database import get_db
from app.models import Komoditas, Penerima, Permintaan
from app.models.enums import PeranPengguna, StatusPermintaan
from app.schemas.permintaan import PermintaanCreate, PermintaanOut

router = APIRouter(prefix="/permintaan", tags=["permintaan"])


def _ke_out(p: Permintaan, db: Session) -> PermintaanOut:
    penerima = db.get(Penerima, p.penerima_id)
    komoditas = db.get(Komoditas, p.komoditas_id)
    return PermintaanOut(
        id=p.id,
        penerima_id=p.penerima_id,
        nama_penerima=penerima.nama if penerima else "",
        komoditas_id=p.komoditas_id,
        nama_komoditas=komoditas.nama if komoditas else "",
        volume_kg=p.volume_kg,
        volume_terpenuhi_kg=p.volume_terpenuhi_kg,
        tanggal_dibutuhkan=p.tanggal_dibutuhkan,
        status=p.status,
        slot_id=p.slot_id,
        dibuat_pada=p.dibuat_pada,
    )


@router.get("", response_model=list[PermintaanOut])
def daftar_permintaan(pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    """Ter-scope per peran (K6): PENERIMA -> miliknya; KOPERASI (& lainnya) -> semua yang terbuka."""
    if pengguna.peran == PeranPengguna.PENERIMA:
        q = db.query(Permintaan).filter_by(penerima_id=pengguna.penerima_id)
    else:
        q = db.query(Permintaan).filter_by(status=StatusPermintaan.TERBUKA)
    baris = q.order_by(Permintaan.dibuat_pada.desc()).all()
    return [_ke_out(p, db) for p in baris]


@router.post("", response_model=PermintaanOut, status_code=201)
def buat_permintaan(body: PermintaanCreate, pengguna=Depends(wajib_peran("PENERIMA")), db: Session = Depends(get_db)):
    komoditas = db.get(Komoditas, body.komoditas_id)
    if komoditas is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Komoditas tidak ditemukan")
    permintaan = Permintaan(
        penerima_id=pengguna.penerima_id,
        komoditas_id=body.komoditas_id,
        volume_kg=body.volume_kg,
        tanggal_dibutuhkan=body.tanggal_dibutuhkan,
        status=StatusPermintaan.TERBUKA,
    )
    db.add(permintaan)
    db.commit()
    db.refresh(permintaan)
    return _ke_out(permintaan, db)
