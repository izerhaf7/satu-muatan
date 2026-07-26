"""Reset skenario demo (§11.2) — hanya aktif saat DEMO_MODE."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from seed.skenario_demo import reset_ke_awal_demo

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoResetOut(BaseModel):
    pesan: str


@router.post("/reset", response_model=DemoResetOut)
def reset_demo(db: Session = Depends(get_db)):
    """Kembalikan database ke keadaan awal skenario demo (§11.2). Idempoten,
    deterministik — memanggil fungsi bersama `reset_ke_awal_demo` (Fase 3,
    `backend/seed/skenario_demo.py`) supaya CLI (`python seed/skenario_demo.py`)
    dan endpoint ini TIDAK PERNAH berbeda perilaku.

    Data transaksional dikosongkan KECUALI 8 slot riwayat SELESAI (spec §11.1 —
    sumber grafik Dashboard Dampak); master (koperasi, penerima, komoditas,
    pengguna) + tier tetap utuh; konfigurasi dikembalikan ke nilai default seed.
    """
    if not get_settings().demo_mode:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Mode demo tidak aktif")

    reset_ke_awal_demo(db)

    return DemoResetOut(
        pesan="Data direset ke keadaan awal skenario demo (riwayat + konfigurasi default dipertahankan)."
    )
