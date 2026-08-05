"""Skema pendukung alamat (K14): autocomplete wilayah & reverse geocoding."""

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.json_schema import SkipJsonSchema


class SumberAlamat(str, Enum):
    GOOGLE = "GOOGLE"
    LOKAL = "LOKAL"


class StatusSaranAlamat(str, Enum):
    OK = "OK"
    FALLBACK_LOKAL = "FALLBACK_LOKAL"
    PENYEDIA_TIDAK_TERSEDIA = "PENYEDIA_TIDAK_TERSEDIA"
    TIDAK_DITEMUKAN = "TIDAK_DITEMUKAN"


class StatusResolusiAlamat(str, Enum):
    OK = "OK"
    KOORDINAT_TIDAK_PRESISI = "KOORDINAT_TIDAK_PRESISI"
    TIDAK_DITEMUKAN = "TIDAK_DITEMUKAN"


class GranularitasAlamat(str, Enum):
    ALAMAT = "ALAMAT"
    JALAN = "JALAN"
    DESA = "DESA"
    KECAMATAN = "KECAMATAN"
    KABUPATEN_KOTA = "KABUPATEN_KOTA"
    PROVINSI = "PROVINSI"


class ErrorOut(BaseModel):
    detail: str


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
    induk_kode: str | None = None


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
    jarak_meter: float | None = Field(default=None, ge=0)
    keyakinan: float | None = Field(default=None, ge=0, le=1)


class AlamatSaranBias(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "description": "Bias opsional berbentuk titik dan radius lengkap. Server menolak pasangan atau radius parsial."
        }
    )

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    radius_meter: float = Field(gt=0, le=50_000)


class AlamatSaranRequest(BaseModel):
    query: str = Field(min_length=3, max_length=200)
    bias: AlamatSaranBias | None = None


class AlamatSaranItemOut(BaseModel):
    place_id: str = Field(
        min_length=1,
        max_length=256,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._~-]{0,255}$",
        description="Token opaque aman; termasuk token lokal yang dapat diresolusikan tanpa penyedia eksternal.",
    )
    teks_utama: str = Field(min_length=1, max_length=200)
    teks_lengkap: str = Field(min_length=1, max_length=500)
    teks_sekunder: str | None = Field(default=None, max_length=300)
    sumber: SumberAlamat


class AlamatSaranListOut(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "description": "Maksimal lima saran. Status fallback/tidak tersedia memberi UI tindakan aman tanpa mengungkap detail penyedia."
        }
    )

    saran: list[AlamatSaranItemOut] = Field(max_length=5)
    status: StatusSaranAlamat
    pesan: str | None = Field(default=None, max_length=300)


class AlamatResolusiRequest(BaseModel):
    place_id: str = Field(
        min_length=1,
        max_length=256,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._~-]{0,255}$",
        description="Token opaque dari `AlamatSaranOut`; berlaku untuk sumber GOOGLE maupun LOKAL.",
    )


class AlamatResolusiOut(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "description": "Koordinat selalu berpasangan. Server juga menegakkan alamat_lengkap non-null berdasarkan status.",
            "oneOf": [
                {"required": ["lat", "lng"]},
                {"not": {"anyOf": [{"required": ["lat"]}, {"required": ["lng"]}]}},
            ],
        }
    )

    alamat_lengkap: str | None = Field(
        min_length=1,
        max_length=500,
        description="Wajib bernilai untuk status OK dan KOORDINAT_TIDAK_PRESISI; null hanya untuk TIDAK_DITEMUKAN.",
    )
    jalan: str | None = Field(default=None, max_length=200)
    kode_pos: str | None = Field(default=None, max_length=10)
    desa: str | None = Field(default=None, max_length=120)
    kecamatan: str | None = Field(default=None, max_length=120)
    kabupaten_kota: str | None = Field(default=None, max_length=120)
    provinsi: str | None = Field(default=None, max_length=120)
    lat: Annotated[float, Field(ge=-90, le=90)] | SkipJsonSchema[None] = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    lng: Annotated[float, Field(ge=-180, le=180)] | SkipJsonSchema[None] = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    granularitas: GranularitasAlamat | None = None
    sumber: SumberAlamat
    status: StatusResolusiAlamat
    pesan: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def validasi_invarian(self):
        if (self.lat is None) != (self.lng is None):
            raise ValueError("lat dan lng harus hadir bersama")
        if self.status == "TIDAK_DITEMUKAN" and self.alamat_lengkap is not None:
            raise ValueError("alamat_lengkap harus null saat tidak ditemukan")
        if self.status != "TIDAK_DITEMUKAN" and not self.alamat_lengkap:
            raise ValueError("alamat_lengkap wajib untuk hasil yang ditemukan")
        return self
