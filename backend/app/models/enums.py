"""Enum domain — nilai persis mengikuti spec §4.2."""

import enum


class PeranPengguna(str, enum.Enum):
    PETANI = "PETANI"
    KOPERASI = "KOPERASI"
    PENERIMA = "PENERIMA"


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


class SumberPosisi(str, enum.Enum):
    HP_PENGAWAL = "HP_PENGAWAL"
    WEBHOOK_VENDOR = "WEBHOOK_VENDOR"
    SIMULASI = "SIMULASI"
