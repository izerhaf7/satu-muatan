"""Tabel alur konsolidasi: slot, slot_tujuan, permintaan, partisipasi
(spec §4.2 + KEPUTUSAN.md K6)."""

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
from app.models.enums import StatusPartisipasi, StatusPermintaan, StatusSlot


class Slot(Base):
    __tablename__ = "slot"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kode: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    titik_kumpul_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("titik_kumpul.id"), nullable=False)
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
    dibuat_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tujuan: Mapped[list["SlotTujuan"]] = relationship(back_populates="slot", order_by="SlotTujuan.urutan")
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


class Permintaan(Base):
    __tablename__ = "permintaan"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    penerima_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("penerima.id"), nullable=False)
    komoditas_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("komoditas.id"), nullable=False)
    volume_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    tanggal_dibutuhkan: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[StatusPermintaan] = mapped_column(
        Enum(StatusPermintaan, name="status_permintaan"), nullable=False, default=StatusPermintaan.TERBUKA
    )
    slot_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("slot.id"))
    # K6: pelacakan pemenuhan parsial + urutan riwayat
    volume_terpenuhi_kg: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    dibuat_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


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
