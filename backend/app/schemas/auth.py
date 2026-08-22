import enum
import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import PeranPengguna

# Nomor HP Indonesia: diawali 0, lalu 8-13 digit lagi (total 9-14 digit).
# Sama dengan pola nomor seed (mis. "081200000011", 12 digit).
_POLA_NO_HP = re.compile(r"^0\d{8,13}$")


class MasukRequest(BaseModel):
    no_hp: str = Field(examples=["081234567001"])
    pin: str = Field(min_length=6, max_length=6, examples=["123456"])


# PETUGAS sengaja tidak termasuk — peran itu (driver, bisa ambil tugas &
# tandai mutu) hanya lewat seed/petugas lain, bukan pendaftaran mandiri.
PeranDaftar = Literal["PETANI", "PENERIMA"]


class DaftarRequest(BaseModel):
    nama: str = Field(min_length=1, examples=["Wati"])
    no_hp: str = Field(examples=["081234567099"])
    pin: str = Field(min_length=6, max_length=6, examples=["123456"])
    peran: PeranDaftar

    @field_validator("nama")
    @classmethod
    def nama_tidak_kosong(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nama tidak boleh kosong")
        return v

    @field_validator("no_hp")
    @classmethod
    def no_hp_format_valid(cls, v: str) -> str:
        if not _POLA_NO_HP.match(v):
            raise ValueError("Nomor HP harus diawali 0 dan hanya berisi angka (contoh: 081234567890)")
        return v


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
