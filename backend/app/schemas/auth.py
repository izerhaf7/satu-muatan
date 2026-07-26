import enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PeranPengguna


class MasukRequest(BaseModel):
    no_hp: str = Field(examples=["081234567001"])
    pin: str = Field(min_length=6, max_length=6, examples=["123456"])


class AkunDemo(str, enum.Enum):
    """6 akun seed (KEPUTUSAN.md K6). UI menampilkan 4 tombol utama (§9.1);
    Dedi & Ijah dipakai skenario demo langkah 5–6."""

    KOPERASI = "KOPERASI"
    PETANI_ASEP = "PETANI_ASEP"
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
    koperasi_id: UUID | None = None
    penerima_id: UUID | None = None


class TokenResponse(BaseModel):
    token: str
    pengguna: PenggunaOut
