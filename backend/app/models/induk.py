"""Tabel induk: titik_kumpul, pengguna, penerima, komoditas
(spec §4.2 + KEPUTUSAN.md K6, rename v2 §2: koperasi → titik_kumpul)."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import PeranPengguna, StatusSumber, TipePenerima, TipeTitikKumpul


class TitikKumpul(Base):
    """Titik kumpul (§2): tempat panen ditimbang & difoto sebelum berangkat.
    Bisa rumah petani utama (default), gapoktan, koperasi, atau mitra."""

    __tablename__ = "titik_kumpul"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama: Mapped[str] = mapped_column(Text, nullable=False)
    # K6: kode singkat untuk kode slot "SM-YYYYMMDD-CKJ-NN"
    kode: Mapped[str | None] = mapped_column(Text, unique=True)
    tipe: Mapped[TipeTitikKumpul] = mapped_column(
        Enum(TipeTitikKumpul, name="tipe_titik_kumpul"),
        nullable=False,
        default=TipeTitikKumpul.PETANI_UTAMA,
        server_default="PETANI_UTAMA",
    )
    # Petani yang ditunjuk menimbang/memfoto/memberi grade di titik ini (§2.3).
    petugas_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pengguna.id"))
    desa: Mapped[str | None] = mapped_column(Text)
    kecamatan: Mapped[str | None] = mapped_column(Text)
    kabupaten: Mapped[str | None] = mapped_column(Text)
    alamat: Mapped[str] = mapped_column(Text, nullable=False)
    lat: Mapped[float] = mapped_column(nullable=False)
    lng: Mapped[float] = mapped_column(nullable=False)
    dibuat_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Penerima(Base):
    """Titik tujuan kiriman. K13: bukan lagi katalog pembeli terdaftar — petani
    menaruh titik tujuan bebas, dan baris di sini dibuat otomatis kalau belum ada
    tujuan lain yang cukup dekat (lihat `radius_dedup_tujuan_km`)."""

    __tablename__ = "penerima"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama: Mapped[str] = mapped_column(Text, nullable=False)
    tipe: Mapped[TipePenerima] = mapped_column(Enum(TipePenerima, name="tipe_penerima"), nullable=False)
    alamat: Mapped[str] = mapped_column(Text, nullable=False)
    lat: Mapped[float] = mapped_column(nullable=False)
    lng: Mapped[float] = mapped_column(nullable=False)
    # K13: membedakan alamat bentukan sistem dari data induk yang di-seed.
    dibuat_otomatis: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    # K14: kontak & kode pos ikut disimpan — surat jalan mensyaratkan data
    # penerima lengkap, dan kurir butuh nomor yang bisa dihubungi di lapangan.
    telepon: Mapped[str | None] = mapped_column(Text)
    kode_pos: Mapped[str | None] = mapped_column(Text)


class Wilayah(Base):
    """Wilayah administratif Indonesia (K14) — sumber autocomplete alamat.

    Di-seed dari berkas JSON di repo (`seed/data/wilayah_jabar.json`, data
    Kemendagri via wilayah.id). SENGAJA disimpan di database kita sendiri, bukan
    dipanggil dari layanan luar saat runtime: demo harus tetap jalan tanpa
    internet, dan daftar kecamatan bukan sesuatu yang layak bergantung pada
    kuota pihak ketiga.

    `lat`/`lng` hanya terisi untuk wilayah yang koordinatnya kita punya —
    sumber resmi tidak menyertakannya. Yang punya koordinat bisa dipakai
    melompatkan peta; sisanya tetap berguna untuk melengkapi alamat.
    """

    __tablename__ = "wilayah"

    kode: Mapped[str] = mapped_column(Text, primary_key=True)  # kode resmi, mis. "32.05.01"
    nama: Mapped[str] = mapped_column(Text, nullable=False)
    tingkat: Mapped[str] = mapped_column(Text, nullable=False)  # PROVINSI|KABUPATEN|KECAMATAN|DESA
    induk_kode: Mapped[str | None] = mapped_column(Text, index=True)
    # Jalur lengkap siap tampil, mis. "Cikajang, Kabupaten Garut, Jawa Barat".
    jalur: Mapped[str] = mapped_column(Text, nullable=False)
    kode_pos: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column()
    lng: Mapped[float | None] = mapped_column()


class GeokodeCache(Base):
    """Hasil reverse geocoding yang sudah pernah dicari (K14).

    Koordinat dibulatkan jadi kunci, sehingga satu titik demo yang diketuk
    berulang kali tidak pernah memanggil jaringan lebih dari sekali."""

    __tablename__ = "geokode_cache"

    kunci: Mapped[str] = mapped_column(Text, primary_key=True)  # "lat,lng" dibulatkan
    sumber: Mapped[str] = mapped_column(Text, nullable=False)  # GOOGLE | LOKAL
    hasil_json: Mapped[str] = mapped_column(Text, nullable=False)
    dibuat_pada: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Pengguna(Base):
    __tablename__ = "pengguna"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama: Mapped[str] = mapped_column(Text, nullable=False)
    no_hp: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    pin_hash: Mapped[str] = mapped_column(Text, nullable=False)
    peran: Mapped[PeranPengguna] = mapped_column(Enum(PeranPengguna, name="peran_pengguna"), nullable=False)
    titik_kumpul_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("titik_kumpul.id"))
    penerima_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("penerima.id"))
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class Komoditas(Base):
    __tablename__ = "komoditas"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nama: Mapped[str] = mapped_column(Text, nullable=False)
    satuan: Mapped[str] = mapped_column(Text, default="kg", server_default="kg")
    harga_acuan_per_kg: Mapped[int] = mapped_column(Integer, nullable=False)
    # §4/C1: parameter Q10 untuk sisa umur simpan (literatur postharvest, ASUMSI).
    q10: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False, default=Decimal("2.0"), server_default="2.0")
    suhu_acuan_c: Mapped[Decimal] = mapped_column(Numeric(4, 1), nullable=False, default=Decimal("25"), server_default="25")
    umur_simpan_jam: Mapped[int] = mapped_column(Integer, nullable=False)
    laju_susut_per_jam: Mapped[Decimal] = mapped_column(Numeric(6, 5), nullable=False)
    status_sumber: Mapped[StatusSumber] = mapped_column(Enum(StatusSumber, name="status_sumber"), nullable=False)
    catatan_sumber: Mapped[str | None] = mapped_column(Text)
