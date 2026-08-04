"""Endpoint kiriman (spec v2 §3.5) — pencocokan otomatis, alur baru petani."""

from datetime import date
from uuid import UUID  # noqa: F401  (dipakai di anotasi respons)

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import wajib_peran
from app.database import get_db
from app.models import Pengguna
from app.schemas.kiriman import KirimanCreate, KirimanPratinjauResponse, KirimanResponse
from app.services.pencocokan import buat_kiriman, pratinjau_kiriman

router = APIRouter(prefix="/kiriman", tags=["kiriman"])


@router.post("", response_model=KirimanResponse, status_code=201)
def kirim_panen(body: KirimanCreate, pengguna=Depends(wajib_peran("PETANI")), db: Session = Depends(get_db)):
    """Kirim panen — sistem cocokkan ke muatan (baru atau yang sudah ada, §3.4).
    Menggantikan alur 'pilih slot → gabung'.

    K14: hanya PETANI. Petugas adalah driver Satu Muatan — dia menjemput dan
    mengantar panen orang lain, bukan menyetorkan panennya sendiri."""
    return buat_kiriman(db, pengguna, body)


@router.get("/pratinjau", response_model=KirimanPratinjauResponse)
def pratinjau(
    volume_kg: int = Query(gt=0),
    lat: float = Query(),
    lng: float = Query(),
    tanggal: date = Query(),
    pengguna=Depends(wajib_peran("PETANI")),
    db: Session = Depends(get_db),
):
    """Pratinjau §3.4 langkah 3: atap + potensi penghematan SEBELUM berkomitmen."""
    return pratinjau_kiriman(db, pengguna, volume_kg, lat, lng, tanggal)
