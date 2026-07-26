"""Jarak & perencanaan armada (spec §5.1–§5.2, KEPUTUSAN.md K1/K6).

Fase 0: signature beku. Implementasi oleh agent domain-engine (Fase 1), test-first.
"""

from dataclasses import dataclass
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


def jarak_haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Jarak lurus antar dua titik, kilometer."""
    raise NotImplementedError


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
    raise NotImplementedError


def jarak_rute_km(titik: list[tuple[float, float]], faktor_jalan: float) -> float:
    """Jarak rute akumulatif: gudang → tujuan1 → ... → tujuanN.

    Setiap segmen = haversine × faktor_jalan. titik[0] WAJIB gudang koperasi.
    """
    raise NotImplementedError


def biaya_kendaraan(tier: Tier, jarak_km: float) -> int:
    """tarif_dasar + round(tarif_per_km * jarak_km)"""
    raise NotImplementedError


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
    raise NotImplementedError
