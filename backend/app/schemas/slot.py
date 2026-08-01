"""Skema slot — jantung kontrak. SlotDetail dipoll 3 detik oleh layar Detail Slot (§9.4)."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StatusPartisipasi, StatusSlot
from app.schemas.master import TitikKumpulOut


class SlotCreate(BaseModel):
    tanggal_kirim: date
    cutoff_at: datetime
    tujuan: list[UUID] = Field(min_length=1, description="penerima_id, urutan drop dihitung server (nearest-neighbor)")
    permintaan_ids: list[UUID] = Field(default_factory=list, description="permintaan yang hendak dipenuhi slot ini (K6)")


class RuteSegmenOut(BaseModel):
    urutan: int
    penerima_id: UUID
    nama_penerima: str
    jarak_segmen_km: float


class TierRingkasOut(BaseModel):
    kode: str
    nama: str
    kapasitas_kg: int


class RencanaArmadaOut(BaseModel):
    """Rencana armada saat ini — sumber denominator bar kapasitas & petunjuk naik kelas tier (§9.4 butir 4)."""

    tier: list[TierRingkasOut]
    biaya_total: int
    kapasitas_total_kg: int


class PratinjauSlotRequest(BaseModel):
    tujuan: list[UUID] = Field(min_length=1)
    skenario_volume: list[int] = Field(min_length=1, description="mis. [300, 800, 2000]")


class SkenarioHargaOut(BaseModel):
    volume_kg: int
    harga_per_kg: int
    biaya_total: int
    kendaraan: list[str]


class PratinjauSlotResponse(BaseModel):
    jarak_km: float
    rute: list[RuteSegmenOut]
    tabel_harga: list[SkenarioHargaOut]


class PartisipasiOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    petani_id: UUID
    nama_petani: str
    komoditas_id: UUID
    nama_komoditas: str
    volume_kg: int
    harga_atap_per_kg: int  # terkunci saat gabung, TIDAK PERNAH berubah
    harga_final_per_kg: int | None = None
    kembalian_rp: int
    status: StatusPartisipasi
    bergabung_pada: datetime


class SlotItemOut(BaseModel):
    """Item daftar slot (Beranda §9.2) — bar kapasitas butuh numerator+denominator di sini."""

    id: UUID
    kode: str
    tanggal_kirim: date
    cutoff_at: datetime
    status: StatusSlot
    jarak_km: float
    volume_terkunci_kg: int
    kapasitas_rencana_kg: int | None = None
    tier_ringkas: str | None = None  # mis. "VAN" atau "VAN+FUSO"
    jumlah_petani: int


class SlotDetailOut(BaseModel):
    """Layar utama demo (§9.4). waktu_server = penangkal selisih jam perangkat."""

    id: UUID
    kode: str
    status: StatusSlot
    tanggal_kirim: date
    cutoff_at: datetime
    waktu_server: datetime
    jarak_km: float
    titik_kumpul: TitikKumpulOut
    tujuan: list[RuteSegmenOut]
    volume_total_kg: int
    harga_berjalan_per_kg: int | None = None
    rencana_saat_ini: RencanaArmadaOut | None = None
    partisipasi: list[PartisipasiOut]
    atap_saya_per_kg: int | None = None  # terisi kalau yang login petani peserta
    hemat_saya_per_kg: int | None = None  # atap_saya − harga_berjalan, tak pernah negatif
    biaya_total: int | None = None
    harga_final_per_kg: int | None = None
    selisih_jaminan_atap: int = 0  # "Selisih dijamin platform" (§5.5, rename v2 §2)


class GabungRequest(BaseModel):
    komoditas_id: UUID
    volume_kg: int = Field(gt=0)


class GabungResponse(BaseModel):
    partisipasi: PartisipasiOut
    harga_atap_per_kg: int


class GabungPratinjauRequest(BaseModel):
    volume_kg: int = Field(gt=0)


class GabungPratinjauResponse(BaseModel):
    harga_atap_per_kg: int
    harga_berjalan_baru_per_kg: int
    luapan: bool
    pesan: str | None = None


class LuapanKapasitasOut(BaseModel):
    """Body 409 saat gabung memicu luapan (§5.5, K6) — bahan dialog dua pilihan."""

    kode: str = "LUAPAN_KAPASITAS"
    harga_baru_per_kg: int
    jumlah_atap_terdampak: int
    slot_alternatif_id: UUID | None = None
    pesan: str
