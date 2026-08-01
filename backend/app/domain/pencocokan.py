"""Pencocokan otomatis kiriman → kelompok muatan (spec v2 §3/C0).

Modul domain MURNI: tanpa DB, tanpa I/O, tanpa datetime.now(). Koefisien
(radius_koridor_km, jendela_hari) masuk lewat parameter dari tabel konfigurasi.

Alurnya di sistem: petani TIDAK lagi memilih slot — sistem yang mencocokkan.
Fungsi ini adalah bentuk BATCH dari algoritma greedy-nya; service layer
memakai aturan yang sama secara incremental (kiriman baru masuk ke kelompok
yang benihnya cocok, atau membuka kelompok baru), termasuk memecah kelompok
yang kelebihan muatan (§3.2 catatan).
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class Kiriman:
    id: UUID
    lat_tujuan: float
    lng_tujuan: float
    tanggal_siap: date
    volume_kg: int


@dataclass(frozen=True)
class Kelompok:
    kiriman: list[UUID]
    lat_pusat: float
    lng_pusat: float
    tanggal: date
    volume_total_kg: int


def _jarak_haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Jarak lurus antar dua titik, kilometer."""
    import math

    r_bumi_km = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r_bumi_km * math.asin(math.sqrt(min(1.0, a)))


def kelompokkan(
    kiriman: list[Kiriman],
    radius_koridor_km: float,
    jendela_hari: int,
) -> list[Kelompok]:
    """Greedy clustering (spec §3.2). JANGAN pakai optimasi rute atau TSP.

    Algoritma:
      1. Urutkan kiriman berdasarkan tanggal_siap, lalu volume (besar dulu).
      2. Ambil kiriman pertama yang belum berkelompok sebagai benih.
      3. Masukkan semua kiriman lain yang:
           - jarak haversine tujuan ke benih <= radius_koridor_km
           - |tanggal_siap − tanggal benih| <= jendela_hari
      4. Ulangi sampai semua kiriman berkelompok.
      5. Pusat kelompok = rata-rata lat/lng anggota.

    Koefisien dari tabel konfigurasi — jangan hardcode.
    """
    terurut = sorted(kiriman, key=lambda k: (k.tanggal_siap, -k.volume_kg))
    belum = {k.id: k for k in terurut}
    hasil: list[Kelompok] = []

    for benih in terurut:
        if benih.id not in belum:
            continue
        anggota = [benih]
        belum.pop(benih.id)
        # Semua kiriman lain yang cocok dengan BENIH (bukan dengan pusat) —
        # greedy, bukan optimasi (§3.2).
        for calon in terurut:
            if calon.id not in belum:
                continue
            jarak = _jarak_haversine_km(benih.lat_tujuan, benih.lng_tujuan, calon.lat_tujuan, calon.lng_tujuan)
            selisih_hari = abs((calon.tanggal_siap - benih.tanggal_siap).days)
            if jarak <= radius_koridor_km and selisih_hari <= jendela_hari:
                anggota.append(calon)
                belum.pop(calon.id)

        lat_pusat = sum(k.lat_tujuan for k in anggota) / len(anggota)
        lng_pusat = sum(k.lng_tujuan for k in anggota) / len(anggota)
        hasil.append(
            Kelompok(
                kiriman=[k.id for k in anggota],
                lat_pusat=lat_pusat,
                lng_pusat=lng_pusat,
                tanggal=benih.tanggal_siap,
                volume_total_kg=sum(k.volume_kg for k in anggota),
            )
        )

    return hasil
