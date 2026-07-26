"""Reset skenario demo (§11.2) — hanya aktif saat DEMO_MODE."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import JejakPosisi, Lot, Partisipasi, Pengiriman, Permintaan, SerahTerima, Slot, SlotTujuan

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoResetOut(BaseModel):
    pesan: str


@router.post("/reset", response_model=DemoResetOut)
def reset_demo(db: Session = Depends(get_db)):
    """Kembalikan database ke keadaan awal skenario demo. Idempoten, deterministik.

    Fase 1: hapus seluruh data transaksional, pertahankan master (koperasi, penerima,
    komoditas, pengguna) + konfigurasi/tier. Seed skenario penuh (§11.2) ditambahkan
    agent infra-demo di Fase 3.
    """
    if not get_settings().demo_mode:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Mode demo tidak aktif")

    # Urutan wajib mengikuti dependensi FK (anak sebelum induk).
    db.query(SerahTerima).delete(synchronize_session=False)
    db.query(JejakPosisi).delete(synchronize_session=False)
    db.query(Lot).delete(synchronize_session=False)
    db.query(Pengiriman).delete(synchronize_session=False)
    db.query(Partisipasi).delete(synchronize_session=False)
    db.query(SlotTujuan).delete(synchronize_session=False)
    db.query(Permintaan).delete(synchronize_session=False)
    db.query(Slot).delete(synchronize_session=False)
    db.commit()

    return DemoResetOut(pesan="Data transaksional direset ke keadaan awal skenario demo.")
