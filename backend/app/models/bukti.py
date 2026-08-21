"""Tabel bukti mutu & pengiriman: lot, serah_terima, pengiriman, jejak_posisi
(spec §4.2 + KEPUTUSAN.md K6)."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import Atribusi, KeputusanSerahTerima, StatusPengiriman, SumberPosisi, SumberTelemetri


class Lot(Base):
    __tablename__ = "lot"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partisipasi_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("partisipasi.id"), nullable=False)
    kode_qr: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    # K6: alokasi lot -> tujuan drop, diisi saat slot ditutup
    penerima_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("penerima.id"))
    berat_aktual_kg: Mapped[int | None] = mapped_column(Integer)
    foto_muat: Mapped[str | None] = mapped_column(Text)  # base64, dikompres client <=800px
    waktu_muat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    catatan_muat: Mapped[str | None] = mapped_column(Text)
    # Input kunci mesin atribusi 3-input (spec v2 §6/C3): grade 1–5 saat muat,
    # dinilai petugas titik kumpul (5 = sangat baik, 1 = tidak layak jual).
    grade_asal: Mapped[int] = mapped_column(Integer, default=5, server_default="5")


class SerahTerima(Base):
    __tablename__ = "serah_terima"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lot.id"), unique=True, nullable=False)
    penerima_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("penerima.id"), nullable=False)
    waktu_bongkar: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    foto_bongkar: Mapped[str | None] = mapped_column(Text)  # base64
    keputusan: Mapped[KeputusanSerahTerima] = mapped_column(
        Enum(KeputusanSerahTerima, name="keputusan_serah_terima"), nullable=False
    )
    # K14: `persen_potongan` DIHAPUS — lihat KeputusanSerahTerima.
    alasan: Mapped[str | None] = mapped_column(Text)
    durasi_transit_menit: Mapped[int] = mapped_column(Integer, nullable=False)
    ambang_transit_menit: Mapped[int] = mapped_column(Integer, nullable=False)
    atribusi: Mapped[Atribusi] = mapped_column(Enum(Atribusi, name="atribusi"), nullable=False)
    # Input atribusi 3-input (spec v2 §6/C3) — disimpan agar penjelasan bisa
    # direkonstruksi persis seperti saat keputusan dibuat.
    grade_tiba: Mapped[int | None] = mapped_column(Integer)
    sisa_umur_simpan_persen: Mapped[int | None] = mapped_column(Integer)
    # K14: indeks mutu yang DILIHAT penerima saat memutuskan — disimpan supaya
    # keputusannya bisa diaudit terhadap angka yang benar-benar dia lihat.
    indeks_mutu: Mapped[int | None] = mapped_column(Integer)


class Pengiriman(Base):
    __tablename__ = "pengiriman"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("slot.id"), unique=True, nullable=False)
    vendor: Mapped[str] = mapped_column(Text, nullable=False)  # 'MOCK' | 'DELIVEREE'
    vendor_ref: Mapped[str | None] = mapped_column(Text)
    # K5: state machine simulasi MockVendor tersimpan di sini
    status_vendor: Mapped[str | None] = mapped_column(Text)
    status_pengiriman: Mapped[StatusPengiriman | None] = mapped_column(Enum(StatusPengiriman, name="status_pengiriman"))
    waktu_berangkat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    waktu_tiba: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    kuotasi_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # Snapshot provider bersifat informasional; tidak pernah menjadi dasar harga.
    rute_polyline: Mapped[str | None] = mapped_column(Text)
    rute_versi: Mapped[int | None] = mapped_column(Integer)
    rute_input_hash: Mapped[str | None] = mapped_column(Text)
    rute_jarak_provider_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))
    rute_durasi_provider_menit: Mapped[int | None] = mapped_column(Integer)
    rute_dihitung_pada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rute_sumber: Mapped[str | None] = mapped_column(Text)
    # K6: timestamp langkah "Dipesan" pada timeline Lacak
    dibuat_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JejakPosisi(Base):
    __tablename__ = "jejak_posisi"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pengiriman_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pengiriman.id"), nullable=False)
    lat: Mapped[float | None] = mapped_column()
    lng: Mapped[float | None] = mapped_column()
    akurasi_m: Mapped[float | None] = mapped_column()
    waktu: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sumber: Mapped[SumberPosisi] = mapped_column(Enum(SumberPosisi, name="sumber_posisi"), nullable=False)


class Telemetri(Base):
    """Sampel suhu/kelembapan per pengiriman (spec v2 §5/C2).

    Sumber SIMULASI dibangkitkan deterministik oleh services/telemetri.py;
    SENSOR/HP_PETUGAS disiapkan untuk masa depan (roadmap, bukan demo)."""

    __tablename__ = "telemetri"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pengiriman_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pengiriman.id"), nullable=False)
    waktu: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    suhu_c: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    kelembapan_persen: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    lat: Mapped[float | None] = mapped_column()
    lng: Mapped[float | None] = mapped_column()
    sumber: Mapped[SumberTelemetri] = mapped_column(Enum(SumberTelemetri, name="sumber_telemetri"), nullable=False)
    sensor_uptime_ms: Mapped[int | None] = mapped_column()
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
