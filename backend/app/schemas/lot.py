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
    grade_asal: int  # grade mutu 1–5 saat muat (spec v2 §6.1)


class MuatPatchRequest(BaseModel):
    berat_aktual_kg: int = Field(gt=0)
    foto_muat_base64: str | None = None  # dikompres client ke <=800px (§3.1)
    grade_asal: int = Field(default=5, ge=1, le=5)  # 5 = sangat baik, 1 = tidak layak jual
    catatan_muat: str | None = None


class SerahTerimaCreate(BaseModel):
    keputusan: KeputusanSerahTerima
    persen_potongan: int = Field(default=0, ge=0, le=100)
    alasan: str | None = None
    foto_bongkar_base64: str | None = None  # K6 — tanpa ini foto_bongkar selamanya NULL
    grade_tiba: int = Field(ge=1, le=5)  # grade mutu 1–5 saat bongkar (spec v2 §6.1)


class SerahTerimaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lot_id: UUID
    penerima_id: UUID
    waktu_bongkar: datetime
    # K10: amandemen pasca-beku oleh arsitek — Berita Acara §9.8 wajib menampilkan
    # foto bongkar; kolomnya terisi via POST serah-terima tapi tidak pernah keluar.
    foto_bongkar: str | None = None  # base64
    keputusan: KeputusanSerahTerima
    persen_potongan: int
    alasan: str | None = None
    durasi_transit_menit: int
    ambang_transit_menit: int
    atribusi: Atribusi
    penjelasan: str  # WAJIB: penjelasan, bukan cuma label (§6)
    grade_asal: int | None = None  # echo dari lot, bahan penjelasan UI (§6.3)
    grade_tiba: int | None = None
    sisa_umur_simpan_persen: int | None = None


class BuktiLotOut(BaseModel):
    """Respons GET /api/lot/qr/{kode_qr} — layar Serah Terima (§9.7)."""

    lot: LotOut
    durasi_transit_berjalan_menit: int | None = None  # dihitung server dari waktu_berangkat
    ambang_transit_menit: int
    serah_terima: SerahTerimaOut | None = None  # terisi kalau sudah diproses (cegah dobel input)
