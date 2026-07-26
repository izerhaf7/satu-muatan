"""Jarak & perencanaan armada (spec §5.1–§5.2, KEPUTUSAN.md K1/K6).

Fase 0: signature beku. Implementasi oleh agent domain-engine (Fase 1), test-first.
"""

import math
from dataclasses import dataclass
from itertools import combinations_with_replacement
from uuid import UUID


class VolumeKosong(ValueError):
    """volume_kg <= 0 — tidak ada yang perlu direncanakan."""


class VolumeTerlaluBesar(ValueError):
    """volume_kg melebihi kapasitas `maks_kendaraan` kendaraan terbesar."""


@dataclass(frozen=True)
class Tier:
    kode: str
    kapasitas_kg: int
    tarif_dasar: int
    tarif_per_km: int


@dataclass(frozen=True)
class RencanaArmada:
    tier: list[Tier]  # bisa >1 kendaraan, bisa campuran (T8: VAN+FUSO)
    biaya_total: int
    kapasitas_total_kg: int


@dataclass(frozen=True)
class TujuanInput:
    penerima_id: UUID
    lat: float
    lng: float


@dataclass(frozen=True)
class TujuanTerurut:
    penerima_id: UUID
    urutan: int  # 1-based, urutan drop
    jarak_segmen_km: float  # haversine × faktor_jalan, dari titik sebelumnya


_R_BUMI_KM = 6371.0  # radius bumi rata-rata — konstanta fisik, bukan koefisien bisnis


def jarak_haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Jarak lurus antar dua titik, kilometer.

    Pembanding: rumus haversine baku (jarak great-circle di permukaan bola
    berjari-jari R_BUMI), spec §5.1.
    """
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return _R_BUMI_KM * c


def urutkan_tujuan_nearest_neighbor(
    gudang: tuple[float, float],
    tujuan: list[TujuanInput],
    faktor_jalan: float,
) -> list[TujuanTerurut]:
    """Urutkan tujuan drop dari gudang dengan nearest-neighbor.

    # Penyederhanaan MVP: nearest-neighbor, bukan TSP optimal.

    Hasil membawa `penerima_id` + `jarak_segmen_km` per kaki rute sehingga
    langsung bisa mengisi baris `slot_tujuan` (KEPUTUSAN.md K6) dan
    jarak_rute_km == sum(t.jarak_segmen_km for t in hasil).
    """
    sisa = list(tujuan)
    posisi_sekarang = gudang
    hasil: list[TujuanTerurut] = []
    urutan = 1

    while sisa:
        # Pembanding: tetangga terdekat dari posisi SEKARANG (bukan dari gudang),
        # itulah "nearest-neighbor" — greedy, bukan TSP optimal.
        terdekat = min(
            sisa,
            key=lambda t: jarak_haversine_km(posisi_sekarang[0], posisi_sekarang[1], t.lat, t.lng),
        )
        jarak_lurus = jarak_haversine_km(posisi_sekarang[0], posisi_sekarang[1], terdekat.lat, terdekat.lng)
        hasil.append(
            TujuanTerurut(
                penerima_id=terdekat.penerima_id,
                urutan=urutan,
                jarak_segmen_km=jarak_lurus * faktor_jalan,
            )
        )
        posisi_sekarang = (terdekat.lat, terdekat.lng)
        sisa.remove(terdekat)
        urutan += 1

    return hasil


def jarak_rute_km(titik: list[tuple[float, float]], faktor_jalan: float) -> float:
    """Jarak rute akumulatif: gudang → tujuan1 → ... → tujuanN.

    Setiap segmen = haversine × faktor_jalan. titik[0] WAJIB gudang koperasi.
    """
    # Pembanding: total rute = Σ jarak antar titik berurutan, tiap kaki
    # dikoreksi faktor_jalan (jarak lurus tidak pernah sama dengan jarak jalan).
    total = 0.0
    for (lat1, lng1), (lat2, lng2) in zip(titik, titik[1:]):
        total += jarak_haversine_km(lat1, lng1, lat2, lng2) * faktor_jalan
    return total


def biaya_kendaraan(tier: Tier, jarak_km: float) -> int:
    """tarif_dasar + round(tarif_per_km * jarak_km)"""
    # Pembanding: struktur tarif Deliveree (tarif dasar tetap + tarif per km),
    # spec §5.2 — dibulatkan matematis (round), bukan ceil/floor.
    return tier.tarif_dasar + round(tier.tarif_per_km * jarak_km)


def rencana_armada(
    volume_kg: int,
    jarak_km: float,
    tiers: list[Tier],
    maks_kendaraan: int,
) -> RencanaArmada:
    """Cari kombinasi kendaraan dengan BIAYA TOTAL TERENDAH berkapasitas >= volume_kg.

    Algoritma (spec §5.2, dikoreksi K1/K6):
      1. Kandidat kendaraan tunggal: semua tier aktif dengan kapasitas >= volume_kg.
      2. Kandidat multi-kendaraan: kombinasi dengan pengulangan hingga
         `maks_kendaraan` (dari konfigurasi, BUKAN konstanta — K6) dari tier aktif.
      3. Pilih biaya terendah. Kalau seri, pilih jumlah kendaraan paling sedikit.
      4. volume_kg <= 0            → raise VolumeKosong        (T9)
         volume_kg tak termuat     → raise VolumeTerlaluBesar  (T10)

    Ruang pencarian kecil (6 tier, maks 4 kendaraan) → exhaustive search boleh.

    Angka acuan WAJIB lulus persis (jarak 80 km, seed §4.2 — KEPUTUSAN.md K1):
      150 kg → MOBIL 271.000 · 300 kg → VAN 332.000 · 600 kg → VAN 332.000
      800 kg → VAN 332.000 · 810/1.000/2.000 kg → ENGKEL 543.000
      4.500 kg → VAN+FUSO 986.000 (kombinasi campuran wajib dipertimbangkan)
      T7: 810 kg wajib MEMBANDINGKAN ENGKEL 543.000 vs VAN+MOBIL 603.000.
    """
    if volume_kg <= 0:
        raise VolumeKosong(f"volume_kg={volume_kg} <= 0, tidak ada yang perlu direncanakan")

    terbaik: tuple[tuple[int, int], tuple[Tier, ...], int, int] | None = None

    # Ruang pencarian kecil (≤6 tier, maks_kendaraan kendaraan) → exhaustive search
    # boleh (spec §5.2): kandidat n=1 = kendaraan tunggal, n>1 = kombinasi
    # multi-kendaraan (termasuk campuran tier berbeda, mis. VAN+FUSO di T8).
    for n in range(1, maks_kendaraan + 1):
        for kombinasi in combinations_with_replacement(tiers, n):
            kapasitas_total = sum(t.kapasitas_kg for t in kombinasi)
            if kapasitas_total < volume_kg:
                continue
            biaya_total = sum(biaya_kendaraan(t, jarak_km) for t in kombinasi)
            # Pembanding: biaya terendah menang; kalau seri, jumlah kendaraan
            # paling sedikit menang (spec §5.2 butir 3) — maka kunci urut (biaya, n).
            kunci = (biaya_total, n)
            if terbaik is None or kunci < terbaik[0]:
                terbaik = (kunci, kombinasi, biaya_total, kapasitas_total)

    if terbaik is None:
        raise VolumeTerlaluBesar(
            f"volume_kg={volume_kg} melebihi kapasitas gabungan maksimal {maks_kendaraan} kendaraan"
        )

    _, kombinasi, biaya_total, kapasitas_total = terbaik
    return RencanaArmada(tier=list(kombinasi), biaya_total=biaya_total, kapasitas_total_kg=kapasitas_total)
