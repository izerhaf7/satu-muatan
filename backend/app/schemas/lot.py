"""Skema lot: muat (§9.5), bukti QR + serah terima (§9.7)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Atribusi, KeputusanSerahTerima


class LotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kode_qr: str
    partisipasi_id: UUID
    nama_petani: str
    nama_komoditas: str
    volume_kg: int  # volume komitmen partisipasi (basis tagihan — K3)
    penerima_id: UUID | None = None
    nama_penerima: str | None = None
    berat_aktual_kg: int | None = None
    foto_muat: str | None = None  # base64
    waktu_muat: datetime | None = None
    catatan_muat: str | None = None
    cacat_terlihat: bool


class MuatPatchRequest(BaseModel):
    berat_aktual_kg: int = Field(gt=0)
    foto_muat_base64: str | None = None  # dikompres client ke <=800px (§3.1)
    cacat_terlihat: bool = False
    catatan_muat: str | None = None


class SerahTerimaCreate(BaseModel):
    keputusan: KeputusanSerahTerima
    persen_potongan: int = Field(default=0, ge=0, le=100)
    alasan: str | None = None
    foto_bongkar_base64: str | None = None  # K6 — tanpa ini foto_bongkar selamanya NULL


class SerahTerimaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lot_id: UUID
    penerima_id: UUID
    waktu_bongkar: datetime
    keputusan: KeputusanSerahTerima
    persen_potongan: int
    alasan: str | None = None
    durasi_transit_menit: int
    ambang_transit_menit: int
    atribusi: Atribusi
    penjelasan: str  # WAJIB: penjelasan, bukan cuma label (§6)


class BuktiLotOut(BaseModel):
    """Respons GET /api/lot/qr/{kode_qr} — layar Serah Terima (§9.7)."""

    lot: LotOut
    durasi_transit_berjalan_menit: int | None = None  # dihitung server dari waktu_berangkat
    ambang_transit_menit: int
    serah_terima: SerahTerimaOut | None = None  # terisi kalau sudah diproses (cegah dobel input)
