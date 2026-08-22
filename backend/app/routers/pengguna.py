"""Endpoint profil operasional pengguna yang sedang masuk."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import wajib_peran
from app.database import get_db
from app.schemas.pengguna import LokasiPenggunaOut, LokasiPenggunaRequest

router = APIRouter(prefix="/pengguna", tags=["pengguna"])


@router.post("/lokasi", response_model=LokasiPenggunaOut)
def perbarui_lokasi_pengguna(
    body: LokasiPenggunaRequest,
    pengguna=Depends(wajib_peran("PETUGAS")),
    db: Session = Depends(get_db),
):
    """Simpan posisi terakhir petugas untuk penyaringan papan tugas."""
    sekarang = datetime.now(timezone.utc)
    pengguna.terkini_lat = body.lat
    pengguna.terkini_lng = body.lng
    pengguna.lokasi_diperbarui_pada = sekarang
    db.commit()
    return LokasiPenggunaOut(lat=body.lat, lng=body.lng, diperbarui_pada=sekarang)
