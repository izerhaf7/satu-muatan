import enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PeranPengguna


class MasukRequest(BaseModel):
    no_hp: str = Field(examples=["081234567001"])
    pin: str = Field(min_length=6, max_length=6, examples=["123456"])


class AkunDemo(str, enum.Enum):
    """Akun demo (v2 §8). Tombol masuk cepat di layar Masuk untuk Petugas/Wati/
    Dedi/Penerima; Ijah masuk manual via nomor HP + PIN di skenario demo."""

    PETUGAS = "PETUGAS"  # Asep — petani yang ditunjuk di Titik Kumpul Pak Asep
    PETANI_WATI = "PETANI_WATI"
    PETANI_DEDI = "PETANI_DEDI"
    PETANI_IJAH = "PETANI_IJAH"
    PENERIMA_CIBIRU = "PENERIMA_CIBIRU"


class MasukDemoRequest(BaseModel):
    akun: AkunDemo


class PenggunaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nama: str
    no_hp: str
    peran: PeranPengguna
    titik_kumpul_id: UUID | None = None
    penerima_id: UUID | None = None


class TokenResponse(BaseModel):
    token: str
    pengguna: PenggunaOut
