from fastapi import APIRouter, Depends

from app.auth import get_pengguna_aktif
from app.routers import stub_fase_0
from app.schemas.auth import MasukDemoRequest, MasukRequest, PenggunaOut, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/masuk", response_model=TokenResponse)
def masuk(body: MasukRequest):
    """Login nomor HP + PIN 6 digit (§9.1)."""
    stub_fase_0()


@router.post("/masuk-demo", response_model=TokenResponse)
def masuk_demo(body: MasukDemoRequest):
    """Masuk cepat (demo) — hanya aktif saat DEMO_MODE (§9.1, K6: 6 akun)."""
    stub_fase_0()


@router.get("/saya", response_model=PenggunaOut)
def saya(pengguna=Depends(get_pengguna_aktif)):
    """Profil pengguna yang sedang login."""
    stub_fase_0()
