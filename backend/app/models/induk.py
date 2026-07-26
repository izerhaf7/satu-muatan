"""Tabel induk: koperasi, pengguna, penerima, komoditas (spec §4.2 + KEPUTUSAN.md K6)."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import PeranPengguna, StatusSumber, TipePenerima


class Koperasi(Base):
    __tablename__ = "koperasi"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama: Mapped[str] = mapped_column(Text, nullable=False)
    # K6: kode singkat untuk kode slot "SM-YYYYMMDD-CKJ-NN"
    kode: Mapped[str | None] = mapped_column(Text, unique=True)
    desa: Mapped[str | None] = mapped_column(Text)
    kecamatan: Mapped[str | None] = mapped_column(Text)
    kabupaten: Mapped[str | None] = mapped_column(Text)
    alamat_gudang: Mapped[str] = mapped_column(Text, nullable=False)
    lat: Mapped[float] = mapped_column(nullable=False)
    lng: Mapped[float] = mapped_column(nullable=False)
    dibuat_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Penerima(Base):
    __tablename__ = "penerima"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama: Mapped[str] = mapped_column(Text, nullable=False)
    tipe: Mapped[TipePenerima] = mapped_column(Enum(TipePenerima, name="tipe_penerima"), nullable=False)
    alamat: Mapped[str] = mapped_column(Text, nullable=False)
    lat: Mapped[float] = mapped_column(nullable=False)
    lng: Mapped[float] = mapped_column(nullable=False)


class Pengguna(Base):
    __tablename__ = "pengguna"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama: Mapped[str] = mapped_column(Text, nullable=False)
    no_hp: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    pin_hash: Mapped[str] = mapped_column(Text, nullable=False)
    peran: Mapped[PeranPengguna] = mapped_column(Enum(PeranPengguna, name="peran_pengguna"), nullable=False)
    koperasi_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("koperasi.id"))
    penerima_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("penerima.id"))
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class Komoditas(Base):
    __tablename__ = "komoditas"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama: Mapped[str] = mapped_column(Text, nullable=False)
    satuan: Mapped[str] = mapped_column(Text, default="kg", server_default="kg")
    harga_acuan_per_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    umur_simpan_jam: Mapped[int] = mapped_column(Integer, nullable=False)
    laju_susut_per_jam: Mapped[Decimal] = mapped_column(Numeric(6, 5), nullable=False)
    status_sumber: Mapped[StatusSumber] = mapped_column(Enum(StatusSumber, name="status_sumber"), nullable=False)
    catatan_sumber: Mapped[str | None] = mapped_column(Text)
