from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import buat_token, get_pengguna_aktif, verifikasi_pin
from app.config import get_settings
from app.database import get_db
from app.models import Pengguna
from app.schemas.auth import AkunDemo, MasukDemoRequest, MasukRequest, PenggunaOut, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Akun demo kanonik (KEPUTUSAN.md K9) — identitas tetap, bukan koefisien bisnis.
_NO_HP_AKUN_DEMO: dict[AkunDemo, str] = {
    AkunDemo.PETUGAS: "081200000001",
    AkunDemo.PETANI_ASEP: "081200000011",
    AkunDemo.PETANI_WATI: "081200000012",
    AkunDemo.PETANI_DEDI: "081200000013",
    AkunDemo.PETANI_IJAH: "081200000014",
    AkunDemo.PENERIMA_CIBIRU: "081200000021",
}


@router.post("/masuk", response_model=TokenResponse)
def masuk(body: MasukRequest, db: Session = Depends(get_db)):
    """Login nomor HP + PIN 6 digit (§9.1)."""
    pengguna = db.query(Pengguna).filter_by(no_hp=body.no_hp).one_or_none()
    if pengguna is None or not pengguna.aktif or not verifikasi_pin(body.pin, pengguna.pin_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Nomor HP atau PIN salah")
    token = buat_token(pengguna.id, pengguna.peran.value)
    return TokenResponse(token=token, pengguna=PenggunaOut.model_validate(pengguna))


@router.post("/masuk-demo", response_model=TokenResponse)
def masuk_demo(body: MasukDemoRequest, db: Session = Depends(get_db)):
    """Masuk cepat (demo) — hanya aktif saat DEMO_MODE (§9.1, K6: 6 akun)."""
    if not get_settings().demo_mode:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Mode demo tidak aktif")
    no_hp = _NO_HP_AKUN_DEMO[body.akun]
    pengguna = db.query(Pengguna).filter_by(no_hp=no_hp).one_or_none()
    if pengguna is None or not pengguna.aktif:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Akun demo belum tersedia — jalankan seed")
    token = buat_token(pengguna.id, pengguna.peran.value)
    return TokenResponse(token=token, pengguna=PenggunaOut.model_validate(pengguna))


@router.get("/saya", response_model=PenggunaOut)
def saya(pengguna=Depends(get_pengguna_aktif)):
    """Profil pengguna yang sedang login."""
    return PenggunaOut.model_validate(pengguna)
