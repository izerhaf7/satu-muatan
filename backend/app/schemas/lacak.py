"""Skema pelacakan (§9.6): timeline Dipesan → Dimuat → Jalan → Tiba,
+ telemetri suhu/kelembapan (spec v2 §5/C2)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import SumberPosisi, SumberTelemetri


class PosisiOut(BaseModel):
    lat: float | None = None
    lng: float | None = None
    waktu: datetime
    sumber: SumberPosisi


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
    timeline: TimelineOut
    estimasi_tiba: datetime | None = None  # dari ambang_transit_menit
    ambang_transit_menit: int
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
