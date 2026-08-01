"""Test domain pencocokan.py — greedy clustering (spec v2 §3.6, P1–P5).

Koordinat uji: Garut–Bandung corridor. 0,01° lintang ≈ 1,11 km.
P4 (pecah kelompok kelebihan muatan) diuji di service layer (§3.2 catatan) —
lihat test_api_kiriman.py.
"""

from datetime import date
from uuid import uuid4

import pytest

from app.domain.pencocokan import Kiriman, kelompokkan

TANGGAL = date(2026, 8, 2)


def _kiriman(lat: float, lng: float, volume: int = 100, tanggal: date = TANGGAL) -> Kiriman:
    return Kiriman(id=uuid4(), lat_tujuan=lat, lng_tujuan=lng, tanggal_siap=tanggal, volume_kg=volume)


def test_p1_tiga_kiriman_dalam_radius_satu_kelompok():
    k = [
        _kiriman(-6.9269, 107.7189, 300),  # Cibiru
        _kiriman(-6.9200, 107.7100, 200),  # ~1,3 km
        _kiriman(-6.9333, 107.7250, 100),  # ~1,0 km
    ]
    hasil = kelompokkan(k, radius_koridor_km=15, jendela_hari=1)
    assert len(hasil) == 1
    assert hasil[0].volume_total_kg == 600
    assert len(hasil[0].kiriman) == 3


def test_p2_dua_kiriman_berjauhan_dua_kelompok():
    k = [
        _kiriman(-6.9269, 107.7189, 300),  # Cibiru
        _kiriman(-7.2830, 107.5000, 200),  # ~44 km
    ]
    hasil = kelompokkan(k, radius_koridor_km=15, jendela_hari=1)
    assert len(hasil) == 2
    assert sorted(kel.volume_total_kg for kel in hasil) == [200, 300]


def test_p3_tujuan_sama_selisih_tanggal_jauh_dua_kelompok():
    k = [
        _kiriman(-6.9269, 107.7189, 300, tanggal=date(2026, 8, 2)),
        _kiriman(-6.9269, 107.7189, 200, tanggal=date(2026, 8, 5)),
    ]
    hasil = kelompokkan(k, radius_koridor_km=15, jendela_hari=1)
    assert len(hasil) == 2


def test_p4_kelompok_besar_tetap_satu_kelompok_di_domain():
    # Pemecahan kelebihan muatan adalah tugas SERVICE layer (§3.2 catatan) —
    # domain mengembalikan kelompok utuh apa adanya.
    k = [_kiriman(-6.9269, 107.7189, 5000), _kiriman(-6.9270, 107.7190, 5000)]
    hasil = kelompokkan(k, radius_koridor_km=15, jendela_hari=1)
    assert len(hasil) == 1
    assert hasil[0].volume_total_kg == 10_000


def test_p5_satu_kiriman_sendirian_satu_kelompok():
    k = [_kiriman(-6.9269, 107.7189, 300)]
    hasil = kelompokkan(k, radius_koridor_km=15, jendela_hari=1)
    assert len(hasil) == 1
    assert hasil[0].volume_total_kg == 300
    assert hasil[0].lat_pusat == pytest.approx(-6.9269)
