"""Test domain armada.py — jarak, urutan tujuan, dan perencanaan armada.

Angka acuan dari KEPUTUSAN.md K1 (tabel T1-T10 terkoreksi) dan K2 (rute demo).
Jarak wajib 80 km, seed tier §4.2, maks_kendaraan=4 kecuali disebutkan lain.
"""

from uuid import uuid4

import pytest

from app.domain.armada import (
    RencanaArmada,
    Tier,
    TujuanInput,
    VolumeKosong,
    VolumeTerlaluBesar,
    biaya_kendaraan,
    jarak_haversine_km,
    jarak_rute_km,
    rencana_armada,
    urutkan_tujuan_nearest_neighbor,
)

JARAK = 80.0
MAKS_KENDARAAN = 4

# Koordinat seed §11.1
GUDANG = (-7.3661, 107.7961)
PANYILEUKAN2 = (-6.9333, 107.6989)
UJUNGBERUNG1 = (-6.9147, 107.7000)
CIBIRU3 = (-6.9269, 107.7189)
FAKTOR_JALAN = 1.3


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
# jarak_haversine_km
# ---------------------------------------------------------------------------


def test_jarak_haversine_km_gudang_ke_panyileukan2():
    # Pembanding: jarak lurus (great-circle) R=6371 km, dihitung independen di luar
    # implementasi lewat rumus haversine baku, lalu dicocokkan ke sini.
    # (Catatan: 49,31 km adalah jarak LURUS; 64,10 km di test rute adalah
    # jarak ini × faktor_jalan 1,30 — dua angka yang berbeda secara sengaja.)
    jarak = jarak_haversine_km(*GUDANG, *PANYILEUKAN2)
    assert jarak == pytest.approx(49.3056, abs=0.01)


def test_jarak_haversine_km_titik_sama_adalah_nol():
    # Pembanding: dua titik identik jaraknya nol.
    assert jarak_haversine_km(*GUDANG, *GUDANG) == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# jarak_rute_km
# ---------------------------------------------------------------------------


def test_jarak_rute_km_rute_demo_seed():
    # Pembanding: KEPUTUSAN.md K2 — rute gudang → Panyileukan2 → Ujungberung1 →
    # Cibiru3 (urutan nearest-neighbor) dengan faktor_jalan 1,30 = 70,03 km.
    titik = [GUDANG, PANYILEUKAN2, UJUNGBERUNG1, CIBIRU3]
    jarak = jarak_rute_km(titik, FAKTOR_JALAN)
    assert jarak == pytest.approx(70.03, abs=0.05)


def test_jarak_rute_km_satu_segmen_sama_dengan_haversine_dikali_faktor():
    # Pembanding: rute dua titik = haversine × faktor_jalan (definisi §5.1).
    titik = [GUDANG, PANYILEUKAN2]
    jarak = jarak_rute_km(titik, FAKTOR_JALAN)
    assert jarak == pytest.approx(jarak_haversine_km(*GUDANG, *PANYILEUKAN2) * FAKTOR_JALAN, rel=1e-9)


# ---------------------------------------------------------------------------
# urutkan_tujuan_nearest_neighbor
# ---------------------------------------------------------------------------


def test_urutkan_tujuan_nearest_neighbor_rute_demo_seed():
    id_panyileukan2 = uuid4()
    id_ujungberung1 = uuid4()
    id_cibiru3 = uuid4()

    # Sengaja dimasukkan tidak berurutan supaya algoritma yang menentukan urutan,
    # bukan urutan input.
    tujuan = [
        TujuanInput(penerima_id=id_cibiru3, lat=CIBIRU3[0], lng=CIBIRU3[1]),
        TujuanInput(penerima_id=id_ujungberung1, lat=UJUNGBERUNG1[0], lng=UJUNGBERUNG1[1]),
        TujuanInput(penerima_id=id_panyileukan2, lat=PANYILEUKAN2[0], lng=PANYILEUKAN2[1]),
    ]

    hasil = urutkan_tujuan_nearest_neighbor(GUDANG, tujuan, FAKTOR_JALAN)

    # Pembanding: KEPUTUSAN.md K2 — nearest-neighbor dari gudang wajib memilih
    # Panyileukan2 dulu (tetangga terdekat), lalu Ujungberung1, lalu Cibiru3.
    assert [t.penerima_id for t in hasil] == [id_panyileukan2, id_ujungberung1, id_cibiru3]
    assert [t.urutan for t in hasil] == [1, 2, 3]

    total = sum(t.jarak_segmen_km for t in hasil)
    assert total == pytest.approx(70.03, abs=0.05)


def test_urutkan_tujuan_nearest_neighbor_jarak_segmen_dari_titik_sebelumnya():
    id_panyileukan2 = uuid4()
    id_ujungberung1 = uuid4()

    tujuan = [
        TujuanInput(penerima_id=id_panyileukan2, lat=PANYILEUKAN2[0], lng=PANYILEUKAN2[1]),
        TujuanInput(penerima_id=id_ujungberung1, lat=UJUNGBERUNG1[0], lng=UJUNGBERUNG1[1]),
    ]

    hasil = urutkan_tujuan_nearest_neighbor(GUDANG, tujuan, FAKTOR_JALAN)

    # Pembanding: segmen pertama = haversine(gudang, Panyileukan2) × faktor;
    # segmen kedua = haversine(Panyileukan2, Ujungberung1) × faktor (BUKAN dari gudang).
    segmen_pertama_acuan = jarak_haversine_km(*GUDANG, *PANYILEUKAN2) * FAKTOR_JALAN
    segmen_kedua_acuan = jarak_haversine_km(*PANYILEUKAN2, *UJUNGBERUNG1) * FAKTOR_JALAN

    assert hasil[0].jarak_segmen_km == pytest.approx(segmen_pertama_acuan, rel=1e-9)
    assert hasil[1].jarak_segmen_km == pytest.approx(segmen_kedua_acuan, rel=1e-9)


# ---------------------------------------------------------------------------
# biaya_kendaraan
# ---------------------------------------------------------------------------


def test_biaya_kendaraan_tabel_seed_80km(tiers_seed):
    # Pembanding: biaya = tarif_dasar + round(tarif_per_km × jarak), spec §5.2.
    by_kode = {t.kode: t for t in tiers_seed}
    assert biaya_kendaraan(by_kode["MOBIL"], JARAK) == 271000
    assert biaya_kendaraan(by_kode["VAN"], JARAK) == 332000
    assert biaya_kendaraan(by_kode["PICKUP"], JARAK) == 390000
    assert biaya_kendaraan(by_kode["BOX"], JARAK) == 375360
    assert biaya_kendaraan(by_kode["ENGKEL"], JARAK) == 543000
    assert biaya_kendaraan(by_kode["FUSO"], JARAK) == 654000


# ---------------------------------------------------------------------------
# rencana_armada — tabel wajib K1 (T1-T10)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "volume_kg,kode_terpilih,biaya_total_acuan",
    [
        (150, ["MOBIL"], 271000),  # T1
        (300, ["VAN"], 332000),  # T2 (K1: VAN, bukan PICKUP)
        (600, ["VAN"], 332000),  # T3 (K1: VAN, bukan PICKUP)
        (800, ["VAN"], 332000),  # T4
        (1000, ["ENGKEL"], 543000),  # T5
        (2000, ["ENGKEL"], 543000),  # T6
    ],
)
def test_rencana_armada_tabel_k1(tiers_seed, volume_kg, kode_terpilih, biaya_total_acuan):
    # Pembanding: tabel angka wajib KEPUTUSAN.md K1 pada jarak 80 km.
    rencana = rencana_armada(volume_kg, JARAK, tiers_seed, MAKS_KENDARAAN)
    assert [t.kode for t in rencana.tier] == kode_terpilih
    assert rencana.biaya_total == biaya_total_acuan


def test_rencana_armada_t7_810kg_engkel_menang_atas_kombinasi_van_mobil(tiers_seed):
    # T7 — mesin WAJIB mempertimbangkan kombinasi multi-kendaraan (VAN+MOBIL),
    # bukan cuma tier tunggal, lalu memilih yang termurah.
    by_kode = {t.kode: t for t in tiers_seed}
    biaya_kombinasi_van_mobil = biaya_kendaraan(by_kode["VAN"], JARAK) + biaya_kendaraan(by_kode["MOBIL"], JARAK)
    assert biaya_kombinasi_van_mobil == 603000  # dihitung manual (K1): 332.000 + 271.000

    rencana = rencana_armada(810, JARAK, tiers_seed, MAKS_KENDARAAN)

    # Pembanding: ENGKEL tunggal (543.000) vs VAN+MOBIL (603.000) — ENGKEL menang
    # karena biayanya lebih rendah, meski kombinasi multi tetap dipertimbangkan.
    assert rencana.biaya_total < biaya_kombinasi_van_mobil
    assert [t.kode for t in rencana.tier] == ["ENGKEL"]
    assert rencana.biaya_total == 543000
    assert rencana.kapasitas_total_kg == 2000


def test_rencana_armada_t8_4500kg_kombinasi_campuran_van_fuso(tiers_seed):
    # T8 — kombinasi campuran (tier berbeda) wajib dipertimbangkan, bukan cuma
    # pengulangan tier yang sama. Pembanding: KEPUTUSAN.md K1, VAN+FUSO termurah.
    rencana = rencana_armada(4500, JARAK, tiers_seed, MAKS_KENDARAAN)
    assert sorted(t.kode for t in rencana.tier) == ["FUSO", "VAN"]
    assert rencana.biaya_total == 986000
    assert rencana.kapasitas_total_kg == 4800

    # Pembanding lain yang harus kalah: FUSO+FUSO (1.308.000) dan ENGKEL×3 (1.629.000).
    by_kode = {t.kode: t for t in tiers_seed}
    biaya_fuso_ganda = biaya_kendaraan(by_kode["FUSO"], JARAK) * 2
    biaya_engkel_triple = biaya_kendaraan(by_kode["ENGKEL"], JARAK) * 3
    assert rencana.biaya_total < biaya_fuso_ganda
    assert rencana.biaya_total < biaya_engkel_triple


def test_rencana_armada_t9_volume_kosong_raise(tiers_seed):
    with pytest.raises(VolumeKosong):
        rencana_armada(0, JARAK, tiers_seed, MAKS_KENDARAAN)


def test_rencana_armada_volume_negatif_raise_volume_kosong(tiers_seed):
    with pytest.raises(VolumeKosong):
        rencana_armada(-50, JARAK, tiers_seed, MAKS_KENDARAAN)


def test_rencana_armada_t10_volume_terlalu_besar_raise(tiers_seed):
    with pytest.raises(VolumeTerlaluBesar):
        rencana_armada(50000, JARAK, tiers_seed, MAKS_KENDARAAN)


def test_rencana_armada_maks_kendaraan_adalah_parameter_bukan_konstanta(tiers_seed):
    # 4.500 kg butuh minimal 2 kendaraan (VAN+FUSO). Dengan maks_kendaraan=1
    # dipaksa satu kendaraan saja — tidak ada tier tunggal berkapasitas cukup,
    # jadi harus meledak sebagai VolumeTerlaluBesar walau tiernya sama.
    with pytest.raises(VolumeTerlaluBesar):
        rencana_armada(4500, JARAK, tiers_seed, 1)

    # Dengan maks_kendaraan=4 (seed), 4.500 kg berhasil direncanakan (T8).
    rencana = rencana_armada(4500, JARAK, tiers_seed, 4)
    assert rencana.biaya_total == 986000


def test_rencana_armada_seri_biaya_pilih_kendaraan_paling_sedikit():
    # Tier sintetis untuk menguji aturan tie-break secara terisolasi (spec §5.2
    # butir 3): A (1 unit, kapasitas 100, biaya 1000) SERI dengan B+B (2 unit,
    # total kapasitas 100, total biaya 1000). Yang menang harus A (lebih sedikit
    # kendaraan), bukan B+B.
    tiers = [
        Tier(kode="A", kapasitas_kg=100, tarif_dasar=1000, tarif_per_km=0),
        Tier(kode="B", kapasitas_kg=50, tarif_dasar=500, tarif_per_km=0),
    ]
    rencana = rencana_armada(100, 10.0, tiers, 4)
    assert [t.kode for t in rencana.tier] == ["A"]
    assert rencana.biaya_total == 1000
