"""Enum domain — nilai persis mengikuti spec §4.2 + spec delta v2 §2/§5/§6."""

import enum


class PeranPengguna(str, enum.Enum):
    PETANI = "PETANI"
    PETUGAS = "PETUGAS"  # dulu KOPERASI — petani yang ditunjuk di titik kumpul (§2.3)
    PENERIMA = "PENERIMA"


class TipeTitikKumpul(str, enum.Enum):
    PETANI_UTAMA = "PETANI_UTAMA"  # rumah/lahan salah satu petani (DEFAULT, §2.2)
    GAPOKTAN = "GAPOKTAN"
    KOPERASI = "KOPERASI"
    MITRA = "MITRA"  # warung, gudang sewa, agen


class TipePenerima(str, enum.Enum):
    SPPG = "SPPG"
    HOREKA = "HOREKA"
    PENGOLAH = "PENGOLAH"
    PASAR_INDUK = "PASAR_INDUK"


class StatusSumber(str, enum.Enum):
    TERVERIFIKASI = "TERVERIFIKASI"
    ASUMSI = "ASUMSI"


class TipeKonfigurasi(str, enum.Enum):
    INT = "INT"
    FLOAT = "FLOAT"
    STRING = "STRING"
    BOOL = "BOOL"


class StatusSlot(str, enum.Enum):
    DIBUKA = "DIBUKA"
    TERKUNCI = "TERKUNCI"
    DIMUAT = "DIMUAT"
    JALAN = "JALAN"
    SELESAI = "SELESAI"
    BATAL = "BATAL"


class StatusPermintaan(str, enum.Enum):
    TERBUKA = "TERBUKA"
    TERPENUHI_SEBAGIAN = "TERPENUHI_SEBAGIAN"
    TERPENUHI = "TERPENUHI"
    KEDALUWARSA = "KEDALUWARSA"


class StatusPartisipasi(str, enum.Enum):
    TERDAFTAR = "TERDAFTAR"
    TERKUNCI = "TERKUNCI"
    DIMUAT = "DIMUAT"
    SELESAI = "SELESAI"
    BATAL = "BATAL"


class KeputusanSerahTerima(str, enum.Enum):
    TERIMA = "TERIMA"
    POTONG = "POTONG"
    TOLAK = "TOLAK"


class Atribusi(str, enum.Enum):
    PETANI = "PETANI"
    LOGISTIK = "LOGISTIK"
    TIDAK_TERBUKTI = "TIDAK_TERBUKTI"
    NORMAL = "NORMAL"  # §6 (C3): tidak ada penurunan mutu — tidak perlu atribusi


class SumberPosisi(str, enum.Enum):
    HP_PENGAWAL = "HP_PENGAWAL"
    WEBHOOK_VENDOR = "WEBHOOK_VENDOR"
    SIMULASI = "SIMULASI"


class SumberTelemetri(str, enum.Enum):
    SIMULASI = "SIMULASI"
    SENSOR = "SENSOR"
    HP_PETUGAS = "HP_PETUGAS"
