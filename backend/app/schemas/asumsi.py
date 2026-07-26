"""Panel Asumsi (spec §9.9): konfigurasi + tier kendaraan, semua ber-badge status_sumber."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import StatusSumber, TipeKonfigurasi


class KonfigurasiOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kunci: str
    nilai: str
    tipe: TipeKonfigurasi
    label: str
    satuan: str | None = None
    status_sumber: StatusSumber
    catatan_sumber: str | None = None


class KonfigurasiPatch(BaseModel):
    nilai: str


class TierKendaraanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kode: str
    nama: str
    kapasitas_kg: int
    tarif_dasar: int
    tarif_per_km: int
    urutan: int
    aktif: bool
    status_sumber: StatusSumber
    catatan_sumber: str | None = None


class TierKendaraanPatch(BaseModel):
    kapasitas_kg: int | None = None
    tarif_dasar: int | None = None
    tarif_per_km: int | None = None
    aktif: bool | None = None
