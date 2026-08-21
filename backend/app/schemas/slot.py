"""Skema slot — jantung kontrak. SlotDetail dipoll 3 detik oleh layar Detail Slot (§9.4)."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StatusPartisipasi, StatusSlot
from app.schemas.master import TitikKumpulOut


# K13: SlotCreate / PratinjauSlot* dihapus — muatan tidak pernah dibuka manusia.


class RuteSegmenOut(BaseModel):
    urutan: int
    penerima_id: UUID
    nama_penerima: str
    jarak_segmen_km: float
    # K13: koordinat ikut dikirim supaya peta tidak perlu mengunduh seluruh buku
    # alamat tujuan (yang kini tumbuh bebas mengikuti kiriman petani).
    lat: float
    lng: float


class RuteJemputOut(BaseModel):
    """K14 — perhentian penjemputan, urut sesuai jalur petugas.

    Inilah yang membuat peran petugas sebagai penghubung terlihat: dia mendapat
    daftar alamat yang harus didatangi, bukan cuma satu titik kumpul abstrak."""

    urutan: int
    partisipasi_id: UUID
    nama_petani: str
    alamat: str
    jarak_segmen_km: float
    lat: float
    lng: float


class TierRingkasOut(BaseModel):
    kode: str
    nama: str
    kapasitas_kg: int


class RencanaArmadaOut(BaseModel):
    """Rencana armada saat ini — sumber denominator bar kapasitas & petunjuk naik kelas tier (§9.4 butir 4)."""

    tier: list[TierRingkasOut]
    biaya_total: int
    kapasitas_total_kg: int


class ResiLotRingkasOut(BaseModel):
    """Resi kanonik satu lot, ditampilkan hanya kepada aktor yang berwenang."""

    lot_id: UUID
    kode_qr: str


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
    # K14: cutoff lewat TIDAK sama dengan slot tertutup — penutupan menetapkan
    # harga final & memesan armada, jadi hanya petugas yang melakukannya. Klien
    # memakai bendera ini supaya tidak lagi menulis "sudah ditutup" pada muatan
    # yang statusnya masih DIBUKA.
    cutoff_lewat: bool = False
    status: StatusSlot
    jarak_km: float
    volume_terkunci_kg: int
    kapasitas_rencana_kg: int | None = None
    tier_ringkas: str | None = None  # mis. "VAN" atau "VAN+FUSO"
    jumlah_petani: int
    resi: list[ResiLotRingkasOut] = []


class SlotDetailOut(BaseModel):
    """Layar utama demo (§9.4). waktu_server = penangkal selisih jam perangkat."""

    id: UUID
    kode: str
    status: StatusSlot
    tanggal_kirim: date
    cutoff_at: datetime
    cutoff_lewat: bool = False
    waktu_server: datetime
    jarak_km: float
    titik_kumpul: TitikKumpulOut
    # K14: rute dua tahap — jemput dulu (kosong untuk muatan gaya lama), lalu antar.
    jemput: list[RuteJemputOut] = []
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
    resi: list[ResiLotRingkasOut] = []


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


class SensorNodeRequest(BaseModel):
    """Path node sensor RTDB. Credential tetap hanya di server."""

    node_path: str = Field(min_length=1)


class SensorNodeOut(BaseModel):
    slot_id: UUID
    node_path: str | None = None
