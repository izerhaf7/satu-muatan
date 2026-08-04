"""Indeks mutu — angka yang dilihat penerima SEBELUM memutuskan (K14).

Sebelumnya sistem sudah menghitung `sisa_umur_simpan_persen` (model Q10 di
`domain/paparan.py`), tetapi angka itu hanya keluar SESUDAH serah terima
disubmit. Penerima memutuskan dalam gelap, lalu diberi tahu hasilnya — urutan
yang terbalik dari maksud produk.

Dua sifat yang membuat indeks ini boleh dipercaya:

1. **Murni dari data terpantau.** Hanya sisa umur simpan (telemetri suhu) dan
   waktu tempuh terhadap ambang rute. Grade tiba TIDAK ikut, karena grade tiba
   adalah penilaian manusia yang baru ada setelah keputusan — memasukkannya akan
   membuat penerima bisa menggerakkan angkanya sendiri.
2. **Tidak ada tuas komersial.** Indeks hanya menentukan apakah tombol TOLAK
   layak muncul. Tidak ada potongan harga, tidak ada tawar-menawar.

Modul domain MURNI (aturan keras CLAUDE.md #2): tanpa DB, tanpa I/O, tanpa
`datetime.now()`. Semua bobot & ambang masuk lewat parameter — dibaca dari tabel
`konfigurasi` oleh pemanggil (aturan keras #1).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class HasilIndeksMutu:
    indeks_mutu: int  # 0–100, makin tinggi makin baik
    penurunan_mutu_persen: int  # 100 − indeks_mutu
    skor_umur_simpan: int  # komponen, ditampilkan supaya angkanya bisa ditelusuri
    skor_transit: int
    boleh_tolak: bool


def _jepit(nilai: float) -> int:
    return int(round(max(0.0, min(100.0, nilai))))


def skor_transit(durasi_menit: int, ambang_menit: int) -> int:
    """100 selama masih di dalam ambang, lalu turun sebanding kelebihannya.

    Kelebihan sebesar satu kali ambang penuh (mis. ambang 180 menit, tempuh 360
    menit) menghabiskan skor jadi 0. Ambang 0 dianggap tidak bisa dinilai —
    kembalikan 100 daripada membagi dengan nol dan menghukum tanpa dasar.
    """
    if ambang_menit <= 0:
        return 100
    kelebihan = max(0, durasi_menit - ambang_menit)
    return _jepit(100.0 * (1.0 - kelebihan / ambang_menit))


def hitung_indeks_mutu(
    sisa_umur_simpan_persen: int,
    durasi_transit_menit: int,
    ambang_transit_menit: int,
    bobot_umur_simpan: float,
    bobot_transit: float,
    ambang_tolak_persen: int,
) -> HasilIndeksMutu:
    """Rata-rata tertimbang dua sinyal terpantau.

        skor_umur    = sisa_umur_simpan_persen
        skor_transit = lihat `skor_transit`
        indeks       = (b_umur × skor_umur + b_transit × skor_transit) / Σbobot
        penurunan    = 100 − indeks
        boleh_tolak  = penurunan > ambang_tolak_persen

    Bobot yang jumlahnya nol tidak masuk akal untuk dinilai; dalam hal itu kedua
    sinyal dianggap sama penting daripada melempar galat di tengah serah terima.
    """
    skor_umur = _jepit(float(sisa_umur_simpan_persen))
    skor_waktu = skor_transit(durasi_transit_menit, ambang_transit_menit)

    total_bobot = bobot_umur_simpan + bobot_transit
    if total_bobot <= 0:
        indeks = _jepit((skor_umur + skor_waktu) / 2)
    else:
        indeks = _jepit((bobot_umur_simpan * skor_umur + bobot_transit * skor_waktu) / total_bobot)

    penurunan = 100 - indeks
    return HasilIndeksMutu(
        indeks_mutu=indeks,
        penurunan_mutu_persen=penurunan,
        skor_umur_simpan=skor_umur,
        skor_transit=skor_waktu,
        # Ketat: LEBIH BESAR dari ambang, bukan sama dengan. Penurunan tepat 50%
        # pada ambang 50 belum cukup untuk menolak satu muatan penuh.
        boleh_tolak=penurunan > ambang_tolak_persen,
    )
