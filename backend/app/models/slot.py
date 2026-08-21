"""Tabel alur konsolidasi: slot, slot_tujuan, partisipasi, kiriman
(spec §4.2 + KEPUTUSAN.md K6; permintaan dihapus di K13)."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import StatusPartisipasi, StatusSlot


class Slot(Base):
    __tablename__ = "slot"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kode: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    titik_kumpul_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("titik_kumpul.id"), nullable=False)
    # K13: petugas (driver Satu Muatan) DITUGASKAN SISTEM saat muatan dibuka —
    # bukan dipilih siapa pun. Dasar otorisasi muat/tutup/majukan.
    petugas_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pengguna.id"))
    tanggal_kirim: Mapped[date] = mapped_column(Date, nullable=False)
    cutoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[StatusSlot] = mapped_column(
        Enum(StatusSlot, name="status_slot"), nullable=False, default=StatusSlot.DIBUKA
    )
    jarak_km: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    tier_terpilih_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tier_kendaraan.id"))
    jumlah_kendaraan: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    # K6: rencana armada lengkap (bisa campuran, mis. VAN+FUSO untuk 4.500 kg).
    # tier_terpilih_id tetap ada sebagai denormalisasi tier dominan untuk UI.
    rencana_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    biaya_total: Mapped[int | None] = mapped_column(Integer)
    harga_final_per_kg: Mapped[int | None] = mapped_column(Integer)
    selisih_jaminan_atap: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    volume_terkunci_kg: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    sensor_node_path: Mapped[str | None] = mapped_column(Text)
    dibuat_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tujuan: Mapped[list["SlotTujuan"]] = relationship(back_populates="slot", order_by="SlotTujuan.urutan")
    # K14: rute punya DUA tahap — jemput dulu, baru antar.
    jemput: Mapped[list["SlotJemput"]] = relationship(back_populates="slot", order_by="SlotJemput.urutan")
    partisipasi: Mapped[list["Partisipasi"]] = relationship(back_populates="slot")


class SlotTujuan(Base):
    __tablename__ = "slot_tujuan"
    __table_args__ = (UniqueConstraint("slot_id", "urutan"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("slot.id"), nullable=False)
    penerima_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("penerima.id"), nullable=False)
    urutan: Mapped[int] = mapped_column(Integer, nullable=False)
    jarak_segmen_km: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)

    slot: Mapped[Slot] = relationship(back_populates="tujuan")


class SlotJemput(Base):
    """Perhentian PENJEMPUTAN satu muatan (K14) — sejajar dengan `SlotTujuan`.

    Sebelumnya seluruh petani dianggap berangkat dari satu titik kumpul, jadi
    petugas tidak pernah tahu ke mana harus menjemput dan jarak yang dihitung
    berbohong: rute sungguhan adalah titik kumpul → semua lokasi jemput → semua
    tujuan, bukan titik kumpul → tujuan saja.
    """

    __tablename__ = "slot_jemput"
    __table_args__ = (UniqueConstraint("slot_id", "urutan"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("slot.id"), nullable=False)
    partisipasi_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("partisipasi.id"), nullable=False)
    urutan: Mapped[int] = mapped_column(Integer, nullable=False)
    lat: Mapped[float] = mapped_column(nullable=False)
    lng: Mapped[float] = mapped_column(nullable=False)
    alamat: Mapped[str] = mapped_column(Text, nullable=False)
    jarak_segmen_km: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)

    slot: Mapped[Slot] = relationship(back_populates="jemput")


class Partisipasi(Base):
    __tablename__ = "partisipasi"
    __table_args__ = (UniqueConstraint("slot_id", "petani_id", "komoditas_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("slot.id"), nullable=False)
    petani_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pengguna.id"), nullable=False)
    komoditas_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("komoditas.id"), nullable=False)
    volume_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    # Dikunci saat join, TIDAK PERNAH berubah (spec §5.3, aturan keras CLAUDE.md #3)
    harga_atap_per_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    harga_final_per_kg: Mapped[int | None] = mapped_column(Integer)
    kembalian_rp: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    status: Mapped[StatusPartisipasi] = mapped_column(
        Enum(StatusPartisipasi, name="status_partisipasi"), nullable=False, default=StatusPartisipasi.TERDAFTAR
    )
    bergabung_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    slot: Mapped[Slot] = relationship(back_populates="partisipasi")


class Kiriman(Base):
    """Kiriman panen dari petani (spec v2 §3/C0) — input pencocokan otomatis.
    Petani TIDAK memilih slot; sistem mencocokkan kiriman ke muatan (baru atau
    yang sudah ada) memakai aturan radius koridor + jendela tanggal."""

    __tablename__ = "kiriman"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    petani_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pengguna.id"), nullable=False)
    komoditas_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("komoditas.id"), nullable=False)
    volume_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    tanggal_siap: Mapped[date] = mapped_column(Date, nullable=False)
    lat_tujuan: Mapped[float] = mapped_column(nullable=False)
    lng_tujuan: Mapped[float] = mapped_column(nullable=False)
    # Ringkasan satu baris — dirakit dari komponen di bawah, tetap dipakai
    # sebagai label pendek di kartu & buku alamat.
    alamat_tujuan: Mapped[str] = mapped_column(Text, nullable=False)

    # K14 — ALAMAT TERSTRUKTUR mengikuti standar ekspedisi Indonesia (nama
    # penerima, telepon, jalan, RT/RW, desa, kecamatan, kota, kode pos, patokan).
    # Satu baris teks bebas tidak cukup: kurir butuh komponen yang bisa dibaca
    # terpisah, dan surat jalan mensyaratkan data pengirim & penerima lengkap.
    nama_penerima: Mapped[str | None] = mapped_column(Text)
    telepon_penerima: Mapped[str | None] = mapped_column(Text)
    jalan_tujuan: Mapped[str | None] = mapped_column(Text)
    rt_rw_tujuan: Mapped[str | None] = mapped_column(Text)
    desa_tujuan: Mapped[str | None] = mapped_column(Text)
    kecamatan_tujuan: Mapped[str | None] = mapped_column(Text)
    kabupaten_tujuan: Mapped[str | None] = mapped_column(Text)
    provinsi_tujuan: Mapped[str | None] = mapped_column(Text)
    kode_pos_tujuan: Mapped[str | None] = mapped_column(Text)
    patokan_tujuan: Mapped[str | None] = mapped_column(Text)

    # K14 — ALAMAT PENJEMPUTAN. Sebelumnya asal kiriman tidak ada sama sekali:
    # semua petani dianggap berangkat dari titik kumpul, sehingga petugas tidak
    # punya alamat untuk dituju dan jarak muatan tidak menghitung leg jemput.
    lat_asal: Mapped[float | None] = mapped_column()
    lng_asal: Mapped[float | None] = mapped_column()
    alamat_asal: Mapped[str | None] = mapped_column(Text)
    telepon_pengirim: Mapped[str | None] = mapped_column(Text)
    jalan_asal: Mapped[str | None] = mapped_column(Text)
    rt_rw_asal: Mapped[str | None] = mapped_column(Text)
    desa_asal: Mapped[str | None] = mapped_column(Text)
    kecamatan_asal: Mapped[str | None] = mapped_column(Text)
    kabupaten_asal: Mapped[str | None] = mapped_column(Text)
    provinsi_asal: Mapped[str | None] = mapped_column(Text)
    kode_pos_asal: Mapped[str | None] = mapped_column(Text)
    patokan_asal: Mapped[str | None] = mapped_column(Text)
    # Hasil pencocokan — terisi begitu kiriman masuk sebuah muatan.
    # K13: penerima_id = titik tujuan hasil resolusi (dipakai ulang atau dibuat
    # otomatis). Inilah dasar alokasi lot → tujuan saat muatan ditutup.
    penerima_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("penerima.id"))
    slot_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("slot.id"))
    partisipasi_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("partisipasi.id"))
    dibuat_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
