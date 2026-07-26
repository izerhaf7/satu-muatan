"""Endpoint pelacakan (§9.6)."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.auth import get_pengguna_aktif, wajib_peran
from app.routers import stub_fase_0
from app.schemas.lacak import PengirimanOut

router = APIRouter(tags=["lacak"])


@router.get("/slot/{slot_id}/pengiriman", response_model=PengirimanOut)
def pengiriman_slot(slot_id: UUID, pengguna=Depends(get_pengguna_aktif)):
    """Timeline + estimasi tiba (dari ambang transit) + jejak posisi."""
    stub_fase_0()


@router.post("/pengiriman/{pengiriman_id}/majukan", response_model=PengirimanOut)
def majukan_pengiriman(pengiriman_id: UUID, pengguna=Depends(wajib_peran("KOPERASI"))):
    """Majukan state simulasi MockVendor satu langkah (K5) — deterministik, untuk demo."""
    stub_fase_0()
