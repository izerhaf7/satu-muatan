"""Tabel acuan mesin harga & Panel Asumsi: tier_kendaraan, konfigurasi (spec §4.2)."""

import uuid

from sqlalchemy import Boolean, Enum, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import StatusSumber, TipeKonfigurasi


class TierKendaraan(Base):
    __tablename__ = "tier_kendaraan"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kode: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    nama: Mapped[str] = mapped_column(Text, nullable=False)
    kapasitas_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    tarif_dasar: Mapped[int] = mapped_column(Integer, nullable=False)
    tarif_per_km: Mapped[int] = mapped_column(Integer, nullable=False)
    urutan: Mapped[int] = mapped_column(Integer, nullable=False)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    status_sumber: Mapped[StatusSumber] = mapped_column(Enum(StatusSumber, name="status_sumber"), nullable=False)
    catatan_sumber: Mapped[str | None] = mapped_column(Text)


class Konfigurasi(Base):
    __tablename__ = "konfigurasi"

    kunci: Mapped[str] = mapped_column(Text, primary_key=True)
    nilai: Mapped[str] = mapped_column(Text, nullable=False)
    tipe: Mapped[TipeKonfigurasi] = mapped_column(Enum(TipeKonfigurasi, name="tipe_konfigurasi"), nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    satuan: Mapped[str | None] = mapped_column(Text)
    status_sumber: Mapped[StatusSumber] = mapped_column(Enum(StatusSumber, name="status_sumber"), nullable=False)
    catatan_sumber: Mapped[str | None] = mapped_column(Text)
