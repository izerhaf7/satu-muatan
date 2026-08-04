"""Test unit `app/domain/mutu.py` (K14) — indeks mutu.

Modul ini murni (tanpa DB/IO/waktu), jadi testnya pun murni: tidak ada fixture,
tidak ada database. Yang dijaga di sini adalah SIFAT-nya, bukan angka hafalan —
kecuali beberapa titik acuan yang memang harus stabil supaya demo terbaca sama
setiap kali dijalankan.
"""

import pytest

from app.domain.mutu import hitung_indeks_mutu, skor_transit

# Bobot acuan = nilai seed (0,7 umur simpan / 0,3 transit), ambang tolak 50%.
BOBOT_UMUR, BOBOT_TRANSIT, AMBANG_TOLAK = 0.7, 0.3, 50


def hitung(sisa: int, durasi: int, ambang: int):
    return hitung_indeks_mutu(sisa, durasi, ambang, BOBOT_UMUR, BOBOT_TRANSIT, AMBANG_TOLAK)


# ---------------------------------------------------------------------------
# skor_transit
# ---------------------------------------------------------------------------


def test_transit_di_dalam_ambang_tidak_dihukum():
    assert skor_transit(100, 180) == 100
    assert skor_transit(180, 180) == 100  # tepat di ambang masih penuh


def test_transit_melewati_ambang_turun_sebanding():
    # Kelebihan setengah ambang → separuh skor hilang.
    assert skor_transit(270, 180) == 50
    # Kelebihan satu ambang penuh → habis.
    assert skor_transit(360, 180) == 0
    # Lebih parah lagi tetap 0, bukan negatif.
    assert skor_transit(1000, 180) == 0


def test_ambang_nol_tidak_menghukum():
    """Rute tanpa ambang tidak bisa dinilai — jangan menghukum tanpa dasar,
    dan jangan membagi dengan nol."""
    assert skor_transit(500, 0) == 100


# ---------------------------------------------------------------------------
# hitung_indeks_mutu
# ---------------------------------------------------------------------------


def test_perjalanan_sempurna_indeks_penuh():
    h = hitung(sisa=100, durasi=60, ambang=180)
    assert h.indeks_mutu == 100
    assert h.penurunan_mutu_persen == 0
    assert h.boleh_tolak is False


def test_indeks_adalah_rata_rata_tertimbang():
    # umur 50, transit 100 → 0,7×50 + 0,3×100 = 65
    h = hitung(sisa=50, durasi=60, ambang=180)
    assert h.skor_umur_simpan == 50
    assert h.skor_transit == 100
    assert h.indeks_mutu == 65
    assert h.penurunan_mutu_persen == 35


def test_penurunan_selalu_pelengkap_indeks():
    for sisa in (0, 13, 47, 88, 100):
        h = hitung(sisa=sisa, durasi=200, ambang=180)
        assert h.penurunan_mutu_persen == 100 - h.indeks_mutu


# ---------------------------------------------------------------------------
# Gerbang TOLAK — inti aturan produk K14
# ---------------------------------------------------------------------------


def test_tolak_tertutup_tepat_di_ambang():
    """Penurunan TEPAT 50% belum cukup untuk menolak satu muatan penuh —
    syaratnya LEBIH BESAR dari ambang, bukan sama dengan."""
    h = hitung(sisa=50, durasi=180, ambang=180)  # 0,7×50 + 0,3×100 = 65
    assert h.penurunan_mutu_persen == 35
    assert h.boleh_tolak is False

    # Rangkai kasus yang penurunannya persis 50: umur 100 & transit 0 → 70;
    # pakai kedua sinyal nol-separuh supaya indeks jatuh tepat ke 50.
    tepat = hitung_indeks_mutu(50, 0, 0, 1.0, 0.0, AMBANG_TOLAK)
    assert tepat.penurunan_mutu_persen == 50
    assert tepat.boleh_tolak is False


def test_tolak_terbuka_di_atas_ambang():
    tepat_lewat = hitung_indeks_mutu(49, 0, 0, 1.0, 0.0, AMBANG_TOLAK)
    assert tepat_lewat.penurunan_mutu_persen == 51
    assert tepat_lewat.boleh_tolak is True


def test_barang_busuk_dan_terlambat_boleh_ditolak():
    h = hitung(sisa=10, durasi=400, ambang=180)
    assert h.boleh_tolak is True


# ---------------------------------------------------------------------------
# Ketahanan
# ---------------------------------------------------------------------------


def test_bobot_nol_jatuh_ke_rata_rata_sama_berat():
    """Bobot yang jumlahnya nol tidak masuk akal untuk dinilai; jangan melempar
    galat di tengah serah terima."""
    h = hitung_indeks_mutu(40, 60, 180, 0.0, 0.0, AMBANG_TOLAK)
    assert h.indeks_mutu == 70  # (40 + 100) / 2


@pytest.mark.parametrize("sisa", [-20, 0, 100, 250])
def test_indeks_selalu_dalam_0_sampai_100(sisa):
    h = hitung(sisa=sisa, durasi=999, ambang=180)
    assert 0 <= h.indeks_mutu <= 100
    assert 0 <= h.penurunan_mutu_persen <= 100
