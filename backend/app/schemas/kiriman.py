"""Skema kiriman (spec v2 §3.5) — pencocokan otomatis, pengganti alur pilih-slot."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class AlamatIn(BaseModel):
    """Alamat terstruktur mengikuti standar penulisan ekspedisi Indonesia (K14).

    Satu baris teks bebas tidak cukup untuk logistik sungguhan: kurir butuh nama
    & nomor telepon yang bisa dihubungi, komponen wilayah yang bisa dibaca
    terpisah, kode pos, dan patokan. Surat jalan pun mensyaratkan data pengirim
    dan penerima yang lengkap, bukan sekadar "Warung Bu Imas".

    Hanya `alamat` (ringkasan) yang wajib — sisanya boleh menyusul supaya petani
    tidak terkunci di formulir panjang saat sedang di kebun.
    """

    alamat: str = Field(min_length=1, max_length=300)
    nama: str | None = Field(default=None, max_length=120)
    telepon: str | None = Field(default=None, max_length=30)
    jalan: str | None = Field(default=None, max_length=200)
    rt_rw: str | None = Field(default=None, max_length=20)
    desa: str | None = Field(default=None, max_length=120)
    kecamatan: str | None = Field(default=None, max_length=120)
    kabupaten: str | None = Field(default=None, max_length=120)
    provinsi: str | None = Field(default=None, max_length=120)
    kode_pos: str | None = Field(default=None, max_length=10)
    patokan: str | None = Field(default=None, max_length=200)


class KirimanCreate(BaseModel):
    komoditas_id: UUID
    # Batas bawah sungguhan (`volume_minimal_kg`) dicek di service, karena
    # nilainya hidup di tabel konfigurasi — bukan konstanta di kode.
    volume_kg: int = Field(gt=0)
    tanggal_siap: date
    # K13: titik tujuan BEBAS — petani menaruh koordinat & alamatnya sendiri,
    # tidak memilih dari katalog penerima terdaftar.
    lat_tujuan: float = Field(ge=-90, le=90)
    lng_tujuan: float = Field(ge=-180, le=180)
    alamat_tujuan: str = Field(min_length=1)
    # K14: rincian alamat tujuan (opsional, melengkapi `alamat_tujuan`).
    rincian_tujuan: AlamatIn | None = None
    # K14: TITIK PENJEMPUTAN. Tanpa ini petugas tidak punya alamat untuk dituju
    # dan jarak muatan tidak menghitung leg penjemputan sama sekali. Opsional
    # supaya kiriman lama & alur ringkas tetap jalan — kalau kosong, muatan
    # berperilaku seperti sebelum K14 (semua berangkat dari titik kumpul).
    lat_asal: float | None = Field(default=None, ge=-90, le=90)
    lng_asal: float | None = Field(default=None, ge=-180, le=180)
    rincian_asal: AlamatIn | None = None


class KirimanResponse(BaseModel):
    slot_id: UUID
    harga_atap_per_kg: int
    harga_berjalan_per_kg: int | None = None
    jumlah_peserta: int
    baru_dibuat: bool


class KirimanPratinjauResponse(BaseModel):
    """Pratinjau §3.4 langkah 3: atap + potensi SEBELUM petani berkomitmen."""

    harga_atap_per_kg: int | None = None
    harga_potensial_per_kg: int | None = None
    slot_cocok_ada: bool
    # K13: jarak rute titik kumpul → tujuan yang diketik petani (bukan lagi
    # jarak ke penerima terdaftar terdekat — katalog itu sudah tidak ada).
    jarak_ke_penerima_km: float | None = None
    pesan: str | None = None  # alasan ditolak / ajakan — bahan copy UI
