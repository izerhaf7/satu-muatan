"""Test domain harga.py — harga atap, harga berjalan, jaminan atap, cek luapan.

Angka acuan dari KEPUTUSAN.md K1 (tabel T1-T11 terkoreksi). Jarak wajib 80 km,
seed tier §4.2, maks_kendaraan=4.
"""

from uuid import uuid4

import pytest

from app.domain.armada import Tier, VolumeKosong, VolumeTerlaluBesar
from app.domain.harga import (
    PartisipasiHarga,
    cek_luapan_kapasitas,
    harga_atap_per_kg,
    harga_berjalan_per_kg,
    tetapkan_harga_final,
)

JARAK = 80.0
MAKS_KENDARAAN = 4


@pytest.fixture
def tiers_seed() -> list[Tier]:
    # Seed §4.2, tarif publik Deliveree (acuan Jawa non-Jabodetabek).
    return [
        Tier(kode="MOBIL", kapasitas_kg=150, tarif_dasar=39000, tarif_per_km=2900),
        Tier(kode="VAN", kapasitas_kg=800, tarif_dasar=92000, tarif_per_km=3000),
        Tier(kode="PICKUP", kapasitas_kg=600, tarif_dasar=110000, tarif_per_km=3500),
        Tier(kode="BOX", kapasitas_kg=800, tarif_dasar=162000, tarif_per_km=2667),
        Tier(kode="ENGKEL", kapasitas_kg=2000, tarif_dasar=279000, tarif_per_km=3300),
        Tier(kode="FUSO", kapasitas_kg=4000, tarif_dasar=350000, tarif_per_km=3800),
    ]


# ---------------------------------------------------------------------------
# harga_atap_per_kg — tabel wajib K1 (harga per kg untuk petani sendirian)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "volume_kg,harga_per_kg_acuan",
    [
        (150, 1807),  # T1
        (300, 1107),  # T2 (K1: VAN, bukan PICKUP 1.300)
        (600, 554),  # T3 (K1: VAN, bukan PICKUP 650)
        (800, 415),  # T4
        (1000, 543),  # T5
        (2000, 272),  # T6
        (810, 671),  # T7
        (4500, 220),  # T8 (VAN+FUSO campuran)
    ],
)
def test_harga_atap_per_kg_tabel_k1(tiers_seed, volume_kg, harga_per_kg_acuan):
    # Pembanding: ceil(biaya_total rencana_armada / volume) — skenario TERBURUK
    # petani (dia sendirian mengirim volume itu), KEPUTUSAN.md K1.
    assert harga_atap_per_kg(volume_kg, JARAK, tiers_seed, MAKS_KENDARAAN) == harga_per_kg_acuan


def test_harga_atap_per_kg_t9_volume_kosong_raise(tiers_seed):
    with pytest.raises(VolumeKosong):
        harga_atap_per_kg(0, JARAK, tiers_seed, MAKS_KENDARAAN)


def test_harga_atap_per_kg_t10_volume_terlalu_besar_raise(tiers_seed):
    with pytest.raises(VolumeTerlaluBesar):
        harga_atap_per_kg(50000, JARAK, tiers_seed, MAKS_KENDARAAN)


# ---------------------------------------------------------------------------
# harga_berjalan_per_kg
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "volume_total_kg,harga_per_kg_acuan",
    [
        (800, 415),
        (1000, 543),
        (2000, 272),
        (4500, 220),
    ],
)
def test_harga_berjalan_per_kg_tabel_k1(tiers_seed, volume_total_kg, harga_per_kg_acuan):
    # Pembanding: sama seperti harga_atap_per_kg (ceil biaya_total/volume), tapi
    # atas volume TERKUNCI SAAT INI (bisa berubah tiap petani baru bergabung).
    assert harga_berjalan_per_kg(volume_total_kg, JARAK, tiers_seed, MAKS_KENDARAAN) == harga_per_kg_acuan


# ---------------------------------------------------------------------------
# cek_luapan_kapasitas (spec §5.5)
# ---------------------------------------------------------------------------


def test_cek_luapan_kapasitas_terdeteksi_saat_800_plus_10(tiers_seed):
    # Pembanding: KEPUTUSAN.md K6 — skenario nyata slot 800 kg (VAN, atap 415)
    # kemasukan 10 kg baru → H_kasar naik ke 671 (ENGKEL), melampaui atap A.
    id_a = uuid4()
    partisipasi = [PartisipasiHarga(id=id_a, volume_kg=800, harga_atap_per_kg=415)]

    hasil = cek_luapan_kapasitas(10, partisipasi, JARAK, tiers_seed, MAKS_KENDARAAN)

    assert hasil.luapan is True
    assert hasil.harga_baru_per_kg == 671
    assert hasil.jumlah_atap_terdampak == 1


def test_cek_luapan_kapasitas_tidak_terdeteksi_saat_300_plus_200(tiers_seed):
    # Pembanding: 300 kg (atap 1.107) + 200 kg baru = 500 kg → tetap di tier VAN
    # (332.000), H_baru = ceil(332.000/500) = 664 < 1.107 atap → TIDAK luapan.
    id_x = uuid4()
    partisipasi = [PartisipasiHarga(id=id_x, volume_kg=300, harga_atap_per_kg=1107)]

    hasil = cek_luapan_kapasitas(200, partisipasi, JARAK, tiers_seed, MAKS_KENDARAAN)

    assert hasil.luapan is False
    assert hasil.harga_baru_per_kg == 664
    assert hasil.jumlah_atap_terdampak == 0


# ---------------------------------------------------------------------------
# tetapkan_harga_final — T11 (jaminan atap), test WAJIB
# ---------------------------------------------------------------------------


def test_tetapkan_harga_final_t11_jaminan_atap(tiers_seed):
    # Pembanding: KEPUTUSAN.md K1 T11 — A bergabung duluan saat slot masih
    # kosong (atap 415 dari VAN 800 kg sendirian), B menyusul 10 kg (atap
    # 27.100). V_total=810 → H_kasar=671, MELAMPAUI atap A. Jaminan atap
    # (spec §5.5) wajib membatasi H_A pada 415, bukan menagih 671.
    id_a, id_b = uuid4(), uuid4()
    partisipasi = [
        PartisipasiHarga(id=id_a, volume_kg=800, harga_atap_per_kg=415),
        PartisipasiHarga(id=id_b, volume_kg=10, harga_atap_per_kg=27100),
    ]

    hasil = tetapkan_harga_final(partisipasi, JARAK, tiers_seed, MAKS_KENDARAAN)

    assert hasil.harga_final_per_kg == 671  # H_kasar yang DITAMPILKAN (spec §5.4 butir 6)
    assert hasil.biaya_total == 543000
    assert [t.kode for t in hasil.rencana.tier] == ["ENGKEL"]

    assert hasil.tagihan == {id_a: 332000, id_b: 6710}
    assert hasil.kembalian == {id_a: 0, id_b: 264290}
    assert hasil.subsidi_koperasi == 204290

    # Invarian: petani tidak pernah ditagih di atas atapnya (CLAUDE.md #3).
    assert hasil.tagihan[id_a] <= 800 * 415
    assert hasil.tagihan[id_b] <= 10 * 27100

    # Invarian: subsidi = biaya_total − Σ tagihan.
    assert hasil.subsidi_koperasi == hasil.biaya_total - sum(hasil.tagihan.values())


def test_tetapkan_harga_final_normal_tanpa_subsidi(tiers_seed):
    # Kondisi normal (tanpa jaminan atap aktif): H_kasar sama dengan atap
    # petani (dia sendirian) → tagihan penuh, kembalian nol, subsidi nol.
    id_a = uuid4()
    partisipasi = [PartisipasiHarga(id=id_a, volume_kg=800, harga_atap_per_kg=415)]

    hasil = tetapkan_harga_final(partisipasi, JARAK, tiers_seed, MAKS_KENDARAAN)

    assert hasil.harga_final_per_kg == 415
    assert hasil.tagihan == {id_a: 332000}
    assert hasil.kembalian == {id_a: 0}
    assert hasil.subsidi_koperasi == 0
