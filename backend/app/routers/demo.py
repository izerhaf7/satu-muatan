"""Reset skenario demo (§11.2) — hanya aktif saat DEMO_MODE."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.routers import stub_fase_0

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoResetOut(BaseModel):
    pesan: str


@router.post("/reset", response_model=DemoResetOut)
def reset_demo():
    """Kembalikan database ke keadaan awal skenario demo. Idempoten, deterministik."""
    stub_fase_0()
