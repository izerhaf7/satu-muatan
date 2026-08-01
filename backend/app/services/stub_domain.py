# STUB FASE 1 — fallback sampai merge fase1/domain; jangan tambah logika bisnis baru di sini.
"""Implementasi sementara algoritma `app.domain.*` (spec §5-§7, KEPUTUSAN.md K1/K6).

`app.services.mesin` memanggil `app.domain.*` (implementasi asli agent domain-engine,
worktree `sm-domain`) terlebih dahulu. Selama fungsi itu masih `raise NotImplementedError`
(yaitu sebelum merge `fase1/domain` -> `fase1/api`), `mesin.py` jatuh ke modul ini supaya
API tetap berfungsi penuh. Begitu domain asli merge, modul ini otomatis tidak lagi dipakai
— tidak ada perubahan kode router yang dibutuhkan.

Algoritma di sini murni mengikuti docstring yang sudah dibekukan Fase 0 di
`app.domain.armada` / `app.domain.harga` / `app.domain.atribusi` / `app.domain.dampak`,
diverifikasi terhadap tabel angka KEPUTUSAN.md K1 (T1-T11). Sama seperti domain asli:
TANPA import DB, TANPA I/O, TANPA datetime.now() — semua koefisien lewat parameter.
"""

import math
from itertools import combinations_with_replacement
from typing import Literal
from uuid import UUID

from app.domain.armada import (
    RencanaArmada,
    Tier,
    TujuanInput,
    TujuanTerurut,
    VolumeKosong,
    VolumeTerlaluBesar,
)
from app.domain.dampak import Dampak, PartisipasiDampak
from app.domain.harga import HasilCekLuapan, HasilPenetapanHarga, PartisipasiHarga

__all__ = [
    "jarak_haversine_km",
    "urutkan_tujuan_nearest_neighbor",
    "jarak_rute_km",
    "biaya_kendaraan",
    "rencana_armada",
    "harga_atap_per_kg",
    "harga_berjalan_per_kg",
    "cek_luapan_kapasitas",
    "tetapkan_harga_final",
    "ambang_transit_menit",
    "tentukan_atribusi",
    "hitung_dampak",
]


def jarak_haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Jarak lurus antar dua titik, kilometer."""
    r_bumi_km = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r_bumi_km * math.asin(math.sqrt(min(1.0, a)))


def urutkan_tujuan_nearest_neighbor(
    gudang: tuple[float, float],
    tujuan: list[TujuanInput],
    faktor_jalan: float,
) -> list[TujuanTerurut]:
    """# Penyederhanaan MVP: nearest-neighbor, bukan TSP optimal."""
    sisa = list(tujuan)
    titik = gudang
    hasil: list[TujuanTerurut] = []
    urutan = 1
    while sisa:
        terdekat = min(sisa, key=lambda t: jarak_haversine_km(titik[0], titik[1], t.lat, t.lng))
        jarak_segmen = jarak_haversine_km(titik[0], titik[1], terdekat.lat, terdekat.lng) * faktor_jalan
        hasil.append(TujuanTerurut(penerima_id=terdekat.penerima_id, urutan=urutan, jarak_segmen_km=jarak_segmen))
        titik = (terdekat.lat, terdekat.lng)
        sisa.remove(terdekat)
        urutan += 1
    return hasil


def jarak_rute_km(titik: list[tuple[float, float]], faktor_jalan: float) -> float:
    """Jarak rute akumulatif: gudang -> tujuan1 -> ... -> tujuanN."""
    total = 0.0
    for i in range(1, len(titik)):
        total += jarak_haversine_km(titik[i - 1][0], titik[i - 1][1], titik[i][0], titik[i][1]) * faktor_jalan
    return total


def biaya_kendaraan(tier: Tier, jarak_km: float) -> int:
    return tier.tarif_dasar + round(tier.tarif_per_km * jarak_km)


def rencana_armada(
    volume_kg: int,
    jarak_km: float,
    tiers: list[Tier],
    maks_kendaraan: int,
) -> RencanaArmada:
    """Exhaustive search: kombinasi-dengan-pengulangan tier aktif hingga `maks_kendaraan`,
    pilih biaya total terendah; seri -> jumlah kendaraan paling sedikit."""
    if volume_kg <= 0:
        raise VolumeKosong("volume_kg <= 0")
    kandidat: list[tuple[int, int, list[Tier], int]] = []
    for n in range(1, maks_kendaraan + 1):
        for kombo in combinations_with_replacement(tiers, n):
            kapasitas = sum(t.kapasitas_kg for t in kombo)
            if kapasitas < volume_kg:
                continue
            biaya = sum(biaya_kendaraan(t, jarak_km) for t in kombo)
            kandidat.append((biaya, n, list(kombo), kapasitas))
    if not kandidat:
        raise VolumeTerlaluBesar(f"volume_kg={volume_kg} melebihi kapasitas {maks_kendaraan} kendaraan terbesar")
    biaya, _n, kombo, kapasitas = min(kandidat, key=lambda k: (k[0], k[1]))
    return RencanaArmada(tier=kombo, biaya_total=biaya, kapasitas_total_kg=kapasitas)


def harga_atap_per_kg(volume_petani_kg: int, jarak_km: float, tiers: list[Tier], maks_kendaraan: int) -> int:
    rencana = rencana_armada(volume_petani_kg, jarak_km, tiers, maks_kendaraan)
    return math.ceil(rencana.biaya_total / volume_petani_kg)


def harga_berjalan_per_kg(volume_total_kg: int, jarak_km: float, tiers: list[Tier], maks_kendaraan: int) -> int:
    rencana = rencana_armada(volume_total_kg, jarak_km, tiers, maks_kendaraan)
    return math.ceil(rencana.biaya_total / volume_total_kg)


def cek_luapan_kapasitas(
    volume_baru_kg: int,
    partisipasi: list[PartisipasiHarga],
    jarak_km: float,
    tiers: list[Tier],
    maks_kendaraan: int,
) -> HasilCekLuapan:
    v_total_baru = sum(p.volume_kg for p in partisipasi) + volume_baru_kg
    rencana = rencana_armada(v_total_baru, jarak_km, tiers, maks_kendaraan)
    h_kasar_baru = math.ceil(rencana.biaya_total / v_total_baru)
    terdampak = sum(1 for p in partisipasi if h_kasar_baru > p.harga_atap_per_kg)
    return HasilCekLuapan(luapan=terdampak > 0, harga_baru_per_kg=h_kasar_baru, jumlah_atap_terdampak=terdampak)


def tetapkan_harga_final(
    partisipasi: list[PartisipasiHarga],
    jarak_km: float,
    tiers: list[Tier],
    maks_kendaraan: int,
) -> HasilPenetapanHarga:
    v_total = sum(p.volume_kg for p in partisipasi)
    rencana = rencana_armada(v_total, jarak_km, tiers, maks_kendaraan)
    h_kasar = math.ceil(rencana.biaya_total / v_total)
    tagihan: dict[UUID, int] = {}
    kembalian: dict[UUID, int] = {}
    for p in partisipasi:
        h_i = min(h_kasar, p.harga_atap_per_kg)  # JAMINAN ATAP §5.5
        tagihan[p.id] = p.volume_kg * h_i
        kembalian[p.id] = p.volume_kg * (p.harga_atap_per_kg - h_i)
    subsidi_koperasi = rencana.biaya_total - sum(tagihan.values())
    return HasilPenetapanHarga(
        harga_final_per_kg=h_kasar,
        biaya_total=rencana.biaya_total,
        rencana=rencana,
        tagihan=tagihan,
        kembalian=kembalian,
        subsidi_koperasi=subsidi_koperasi,
    )


def ambang_transit_menit(jarak_km: float, kecepatan_kmh: int, faktor_toleransi: float) -> int:
    return math.ceil((jarak_km / kecepatan_kmh) * 60 * faktor_toleransi)


def tentukan_atribusi(
    grade_asal: int,
    grade_tiba: int,
    durasi_transit_menit: int,
    ambang_menit: int,
    sisa_umur_simpan_persen: int,
    ambang_grade_asal: int,
    ambang_paparan_persen: int,
) -> Literal["PETANI", "LOGISTIK", "TIDAK_TERBUKTI", "NORMAL"]:
    if grade_asal < ambang_grade_asal:
        return "PETANI"
    if grade_tiba >= grade_asal:
        return "NORMAL"
    if durasi_transit_menit > ambang_menit or sisa_umur_simpan_persen < ambang_paparan_persen:
        return "LOGISTIK"
    return "TIDAK_TERBUKTI"


def hitung_dampak(
    jumlah_partisipan: int,
    jarak_km: float,
    partisipasi: list[PartisipasiDampak],
    faktor_emisi: float,
    laju_susut_per_jam: dict[UUID, float],
    jam_dihemat: float | None,
) -> Dampak:
    truk_km_dihemat = max(jumlah_partisipan - 1, 0) * jarak_km
    emisi_dihemat_kg_co2 = truk_km_dihemat * faktor_emisi
    penghematan_ongkos_rp = sum(p.volume_kg * (p.harga_atap_per_kg - p.harga_final_per_kg) for p in partisipasi)
    susut_dicegah_kg: float | None
    if jam_dihemat is None or jam_dihemat <= 0 or not partisipasi:
        susut_dicegah_kg = None
    else:
        susut_dicegah_kg = sum(
            p.volume_kg * laju_susut_per_jam.get(p.komoditas_id, 0.0) * jam_dihemat for p in partisipasi
        )
    return Dampak(
        truk_km_dihemat=truk_km_dihemat,
        emisi_dihemat_kg_co2=emisi_dihemat_kg_co2,
        penghematan_ongkos_rp=int(round(penghematan_ongkos_rp)),
        susut_dicegah_kg=susut_dicegah_kg,
    )


def persen_penghematan_ongkos(partisipasi: list[PartisipasiDampak]) -> float | None:
    total_atap = sum(p.volume_kg * p.harga_atap_per_kg for p in partisipasi)
    if total_atap <= 0:
        return None
    total_final = sum(p.volume_kg * p.harga_final_per_kg for p in partisipasi)
    return (total_atap - total_final) / total_atap * 100
