"""Test domain paparan.py — sisa umur simpan model Q10 (spec v2 §4.4, E1–E6).

Angka acuan §4.3: sawi 3 jam bak ±35 °C -> f = 3,5 -> jam_ekivalen 10,5 ->
sisa 25,5 jam -> ~71%. Mesin yang benar; dokumen menyesuaikan.
"""

import pytest

from app.domain.paparan import SampelTelemetri, hitung_paparan


def _sampel(suhu: float, menit: int, kelembapan: float = 70.0) -> SampelTelemetri:
    return SampelTelemetri(suhu_c=suhu, kelembapan_persen=kelembapan, menit_sejak_sebelumnya=menit)


def test_e1_suhu_tepat_acuan_ekivalen_sama_nyata():
    hasil = hitung_paparan([_sampel(25, 60), _sampel(25, 60)], q10=3.5, suhu_acuan_c=25, umur_simpan_jam=36)
    assert hasil.jam_ekivalen == pytest.approx(hasil.jam_nyata)
    assert hasil.jam_nyata == pytest.approx(2.0)


def test_e2_sepuluh_derajat_di_atas_acuan_q10_2():
    hasil = hitung_paparan([_sampel(35, 120)], q10=2, suhu_acuan_c=25, umur_simpan_jam=36)
    assert hasil.jam_ekivalen == pytest.approx(2 * hasil.jam_nyata)


def test_e3_sepuluh_derajat_di_bawah_acuan_q10_2():
    hasil = hitung_paparan([_sampel(15, 120)], q10=2, suhu_acuan_c=25, umur_simpan_jam=36)
    assert hasil.jam_ekivalen == pytest.approx(0.5 * hasil.jam_nyata)


def test_e4_paparan_melebihi_umur_simpan_sisa_nol():
    hasil = hitung_paparan([_sampel(35, 180)], q10=2, suhu_acuan_c=25, umur_simpan_jam=1)
    assert hasil.sisa_umur_simpan_jam == 0
    assert hasil.sisa_umur_simpan_persen == 0


def test_e5_daftar_sampel_kosong():
    hasil = hitung_paparan([], q10=3.5, suhu_acuan_c=25, umur_simpan_jam=36)
    assert hasil.jam_ekivalen == 0
    assert hasil.sisa_umur_simpan_persen == 100


def test_e6_sawi_3_jam_35_derajat():
    # Acuan demo §4.3: bak terbuka ±35 °C selama 3 jam, q10 3,5, umur 36 jam.
    sampel = [_sampel(35, 60), _sampel(35, 60), _sampel(35, 60)]
    hasil = hitung_paparan(sampel, q10=3.5, suhu_acuan_c=25, umur_simpan_jam=36)
    assert hasil.jam_ekivalen == pytest.approx(10.5)
    assert hasil.sisa_umur_simpan_jam == pytest.approx(25.5)
    assert 65 <= hasil.sisa_umur_simpan_persen <= 75
