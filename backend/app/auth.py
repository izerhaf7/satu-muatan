"""Auth sederhana: login nomor HP + PIN 6 digit, JWT HS256 (spec §3.1).
Tiga peran, cek lewat dependency — tanpa sistem izin rumit (spec §12)."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db

_bearer = HTTPBearer(auto_error=False)


def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode(), bcrypt.gensalt()).decode()


def verifikasi_pin(pin: str, pin_hash: str) -> bool:
    return bcrypt.checkpw(pin.encode(), pin_hash.encode())


def buat_token(pengguna_id: UUID, peran: str) -> str:
    settings = get_settings()
    payload = {
        "sub": str(pengguna_id),
        "peran": peran,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_kadaluarsa_menit),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def get_pengguna_aktif(
    kredensial: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
):
    """Dependency: pengguna login (objek models.Pengguna)."""
    from app.models import Pengguna  # import lokal menghindari siklus

    if kredensial is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Belum masuk")
    try:
        payload = jwt.decode(kredensial.credentials, get_settings().jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token tidak sah")
    pengguna = db.get(Pengguna, UUID(payload["sub"]))
    if pengguna is None or not pengguna.aktif:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Akun tidak aktif")
    return pengguna


def wajib_peran(*peran: str):
    """Dependency factory: batasi endpoint ke peran tertentu.
    Contoh: Depends(wajib_peran("PETUGAS"))"""

    def _cek(pengguna=Depends(get_pengguna_aktif)):
        if pengguna.peran.value not in peran:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Peran tidak diizinkan")
        return pengguna

    return _cek
