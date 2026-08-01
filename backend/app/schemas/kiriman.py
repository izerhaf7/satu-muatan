"""Skema kiriman (spec v2 §3.5) — pencocokan otomatis, pengganti alur pilih-slot."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class KirimanCreate(BaseModel):
    komoditas_id: UUID
    volume_kg: int = Field(gt=0)
    tanggal_siap: date
    lat_tujuan: float
    lng_tujuan: float
    alamat_tujuan: str = Field(min_length=1)


class KirimanResponse(BaseModel):
    slot_id: UUID
    harga_atap_per_kg: int
    harga_berjalan_per_kg: int | None = None
    jumlah_peserta: int
    baru_dibuat: bool


class KirimanPratinjauResponse(BaseModel):
    """Pratinjau §3.4 langkah 3: atap + potensi SEBELUM petani berkomitmen."""

    harga_atap_per_kg: int | None = None
    harga_potensial_per_kg: int | None = None
    slot_cocok_ada: bool
    penerima_terdekat_id: UUID | None = None
    nama_penerima_terdekat: str | None = None
    jarak_ke_penerima_km: float | None = None
    pesan: str | None = None  # mis. "di luar koridor" — bahan copy UI
