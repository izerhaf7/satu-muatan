"""Enum domain — nilai persis mengikuti spec §4.2 + spec delta v2 §2/§5/§6."""

import enum


class PeranPengguna(str, enum.Enum):
    PETANI = "PETANI"
    # K13: petugas = driver Satu Muatan yang mengecek & mengoordinasikan petani
    # dengan komoditasnya, lalu membawa muatannya. Ditugaskan sistem per muatan.
    PETUGAS = "PETUGAS"
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


class StatusPengiriman(str, enum.Enum):
    """State machine pengiriman driver dan penerima."""

    MUAT = "MUAT"
    ANTAR = "ANTAR"
    BONGKAR_MUAT = "BONGKAR_MUAT"
    SELESAI = "SELESAI"


class StatusPartisipasi(str, enum.Enum):
    TERDAFTAR = "TERDAFTAR"
    TERKUNCI = "TERKUNCI"
    DIMUAT = "DIMUAT"
    SELESAI = "SELESAI"
    # K14: lot yang DITOLAK penerima tidak boleh tercatat "SELESAI" — barangnya
    # tidak diterima. Sebelumnya penolakan tetap menutup partisipasi sebagai
    # selesai, sehingga riwayat petani berbohong tentang apa yang terjadi.
    DITOLAK = "DITOLAK"
    BATAL = "BATAL"


class KeputusanSerahTerima(str, enum.Enum):
    """K14: POTONG DIHAPUS. Penerima tidak boleh punya tuas komersial.

    "Terima dengan potongan" membuat penerima bisa menekan harga sepihak dengan
    alasan mutu yang dia nilai sendiri — dan selama ini `persen_potongan` bahkan
    tidak pernah memengaruhi pembayaran, jadi ia murni ruang tawar-menawar tanpa
    akibat yang tercatat. Pilihannya kini hanya TERIMA atau TOLAK, dan TOLAK
    hanya terbuka kalau penurunan mutu yang DIUKUR SISTEM melewati ambang."""

    TERIMA = "TERIMA"
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
