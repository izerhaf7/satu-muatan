"""Skema pendukung alamat (K14): autocomplete wilayah & reverse geocoding."""

from pydantic import BaseModel


class WilayahOut(BaseModel):
    kode: str
    nama: str
    tingkat: str  # DESA | KECAMATAN | KABUPATEN | PROVINSI
    jalur: str  # siap tampil, mis. "Cikajang, Kabupaten Garut, Jawa Barat"
    kode_pos: str | None = None
    # Terisi hanya untuk wilayah yang koordinatnya kita punya — sumber resmi
    # tidak menyertakannya. Klien memakai ini untuk melompatkan peta.
    lat: float | None = None
    lng: float | None = None


class GeokodeOut(BaseModel):
    alamat: str
    desa: str | None = None
    kecamatan: str | None = None
    kabupaten: str | None = None
    provinsi: str | None = None
    kode_pos: str | None = None
    # GOOGLE = alamat presisi; LOKAL = wilayah terdekat dari data kita sendiri.
    # Dinyatakan apa adanya supaya UI bisa jujur soal tingkat kepastiannya.
    sumber: str
