"""Skema pelacakan (§9.6): timeline Dipesan → Dimuat → Jalan → Tiba,
+ telemetri suhu/kelembapan (spec v2 §5/C2)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import StatusPengiriman, SumberPosisi, SumberTelemetri


class PosisiOut(BaseModel):
    lat: float | None = None
    lng: float | None = None
    waktu: datetime
    sumber: SumberPosisi
    akurasi_m: float | None = None


class TimelineOut(BaseModel):
    dipesan: datetime | None = None  # pengiriman.dibuat_pada (K6)
    dimuat: datetime | None = None
    berangkat: datetime | None = None
    tiba: datetime | None = None


class PengirimanOut(BaseModel):
    id: UUID
    slot_id: UUID
    vendor: str
    vendor_ref: str | None = None
    status_vendor: str | None = None
    status_pengiriman: StatusPengiriman | None = None
    timeline: TimelineOut
    estimasi_tiba: datetime | None = None  # dari rute_durasi_provider_menit; jatuh ke ambang_transit_menit
    ambang_transit_menit: int
    # T5: durasi/jarak rute provider (Google/haversine) — basis `estimasi_tiba`
    # kalau tersedia; `ambang_transit_menit` tetap dipakai attribusi/mutu/dampak.
    eta_provider_menit: int | None = None
    jarak_provider_km: float | None = None
    jejak: list[PosisiOut]
    rute_polyline: str | None = None
    rute_versi: int | None = None
    eta_sumber: str | None = None
    eta_dihitung_pada: datetime | None = None


class TelemetriSampelOut(BaseModel):
    waktu: datetime
    suhu_c: float
    kelembapan_persen: float
    lat: float | None = None
    lng: float | None = None
    sumber: SumberTelemetri
    sensor_uptime_ms: int | None = None
    received_at: datetime | None = None


class TelemetriRingkasanOut(BaseModel):
    """Ringkasan paparan perjalanan — bahan 3 kartu + garis ambang di grafik (§5.4)."""

    suhu_maks_c: float
    suhu_rata_c: float
    kelembapan_rata_persen: float
    jam_ekivalen: float
    sisa_umur_simpan_persen: int
    suhu_acuan_c: float  # garis ambang di grafik suhu
    nama_komoditas: str | None = None  # komoditas dominan (basis q10/umur simpan)


class TelemetriOut(BaseModel):
    sampel: list[TelemetriSampelOut]
    ringkasan: TelemetriRingkasanOut | None = None  # None sebelum berangkat


class TitikPetaOut(BaseModel):
    nama: str
    lat: float
    lng: float


class PerjalananResiOut(BaseModel):
    """K14 — seluruh perjalanan satu resi dalam sekali panggil.

    Penerima berhak melihat SELURUH data perjalanan sebelum memutuskan menerima
    atau menolak; sebelumnya ia hanya mendapat dua angka ringkas dan grafiknya
    cuma bisa dibuka peran lain."""

    pengiriman: PengirimanOut
    telemetri: TelemetriOut
    titik_kumpul: TitikPetaOut
    tujuan: list[TitikPetaOut]


class KoordinatTiba(BaseModel):
    lat: float
    lng: float


class SampaiRequest(BaseModel):
    """T8 — body opsional endpoint `sampai`: koordinat GPS petugas saat
    menyatakan tiba. Tanpa koordinat, kedatangan diterima begitu saja."""

    koordinat: KoordinatTiba | None = None


class KoordinatPengiriman(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class StatusPengirimanRequest(BaseModel):
    """Driver mengirim MUAT, ANTAR, atau BONGKAR_MUAT.

    SELESAI ditetapkan hanya setelah serah-terima penerima beratribusi.
    """

    status: Literal["MUAT", "ANTAR", "BONGKAR_MUAT"]
    koordinat: KoordinatPengiriman | None = None


class PosisiPengirimanRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    akurasi_m: float | None = Field(default=None, ge=0)
    waktu: datetime | None = None
