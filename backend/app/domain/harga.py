"""Mesin harga: atap, berjalan, penetapan final, jaminan atap, cek luapan
(spec §5.3–§5.5, KEPUTUSAN.md K1/K6).

Fase 0: signature beku. Implementasi oleh agent domain-engine (Fase 1), test-first.
"""

import math
from dataclasses import dataclass
from uuid import UUID

from app.domain.armada import RencanaArmada, Tier, rencana_armada


@dataclass(frozen=True)
class PartisipasiHarga:
    """Input minimal penetapan harga (spec §5.3)."""

    id: UUID
    volume_kg: int
    harga_atap_per_kg: int


@dataclass(frozen=True)
class HasilPenetapanHarga:
    harga_final_per_kg: int  # H_kasar yang DITAMPILKAN (spec §5.4 butir 6)
    biaya_total: int
    rencana: RencanaArmada
    tagihan: dict[UUID, int]  # partisipasi_id → rupiah
    kembalian: dict[UUID, int]  # partisipasi_id → rupiah
    subsidi_koperasi: int


@dataclass(frozen=True)
class HasilCekLuapan:
    luapan: bool
    harga_baru_per_kg: int  # H_kasar seandainya volume baru ikut
    jumlah_atap_terdampak: int  # berapa peserta yang atapnya akan terlampaui


def harga_atap_per_kg(volume_petani_kg: int, jarak_km: float, tiers: list[Tier], maks_kendaraan: int) -> int:
    """Harga yang dikunci untuk seorang petani saat ia bergabung.

    Definisi: biaya kalau DIA SENDIRIAN mengirim volume itu (opsi TERMURAH untuknya —
    aturan min-cost, KEPUTUSAN.md K1). Ini skenario terburuk bagi si petani.
    Dibulatkan KE ATAS (ceil) — jangan pernah menjanjikan lebih murah dari yang mungkin.

    Acuan: 300 kg @80 km → ceil(332.000/300) = 1.107 (VAN, bukan PICKUP — K1).
    """
    # Pembanding: rencana_armada termurah untuk volume itu SENDIRIAN, dibagi
    # volume, dibulatkan ke atas — jangan pernah menjanjikan lebih murah dari
    # yang benar-benar bisa direalisasikan.
    rencana = rencana_armada(volume_petani_kg, jarak_km, tiers, maks_kendaraan)
    return math.ceil(rencana.biaya_total / volume_petani_kg)


def harga_berjalan_per_kg(volume_total_kg: int, jarak_km: float, tiers: list[Tier], maks_kendaraan: int) -> int:
    """Harga per kg dengan volume terkunci saat ini. Dibulatkan ke atas (ceil)."""
    # Pembanding: definisi sama dengan harga_atap_per_kg (ceil biaya/volume),
    # bedanya volume di sini adalah total slot SAAT INI, bukan volume solo
    # seorang petani — turun tiap kali ada petani baru bergabung (spec §5.3).
    rencana = rencana_armada(volume_total_kg, jarak_km, tiers, maks_kendaraan)
    return math.ceil(rencana.biaya_total / volume_total_kg)


def cek_luapan_kapasitas(
    volume_baru_kg: int,
    partisipasi: list[PartisipasiHarga],
    jarak_km: float,
    tiers: list[Tier],
    maks_kendaraan: int,
) -> HasilCekLuapan:
    """Deteksi §5.5: apakah bergabungnya volume baru membuat H_kasar baru
    melampaui harga_atap peserta yang SUDAH ada?

    Kalau ya → API mengembalikan 409 LUAPAN_KAPASITAS dan UI menawarkan dua
    pilihan (slot berikutnya / buka slot kedua). Ini BUKAN edge case teoretis:
    pada slot ~800 kg ini terjadi di demo (800 kg → VAN 415/kg; +10 kg →
    ENGKEL, H_kasar 671 > atap 415).
    """
    volume_total_baru = sum(p.volume_kg for p in partisipasi) + volume_baru_kg
    rencana_baru = rencana_armada(volume_total_baru, jarak_km, tiers, maks_kendaraan)
    h_baru = math.ceil(rencana_baru.biaya_total / volume_total_baru)

    # Pembanding: peserta LAMA yang atapnya sendiri akan terlampaui oleh
    # H_kasar baru — merekalah yang butuh jaminan atap kalau volume baru ini
    # benar-benar bergabung.
    jumlah_atap_terdampak = sum(1 for p in partisipasi if h_baru > p.harga_atap_per_kg)

    return HasilCekLuapan(
        luapan=jumlah_atap_terdampak > 0,
        harga_baru_per_kg=h_baru,
        jumlah_atap_terdampak=jumlah_atap_terdampak,
    )


def tetapkan_harga_final(
    partisipasi: list[PartisipasiHarga],
    jarak_km: float,
    tiers: list[Tier],
    maks_kendaraan: int,
) -> HasilPenetapanHarga:
    """Penetapan harga saat cutoff (spec §5.4 + JAMINAN ATAP §5.5).

    1. V_total   = Σ volume_kg
    2. rencana   = rencana_armada(V_total, jarak_km, tiers, maks_kendaraan)
    3. H_kasar   = ceil(rencana.biaya_total / V_total)
    4. Untuk tiap partisipasi i:
           H_i         = min(H_kasar, harga_atap_i)   ← JAMINAN ATAP
           tagihan_i   = volume_i × H_i
           kembalian_i = volume_i × (harga_atap_i − H_i)
    5. subsidi_koperasi = biaya_total − Σ tagihan_i
           (0 normal; > 0 hanya saat jaminan atap aktif — tampil terbuka di UI
           koperasi sebagai "Selisih ditanggung koperasi")
    6. harga_final_per_kg yang ditampilkan = H_kasar

    Basis penagihan = volume komitmen partisipasi.volume_kg; berat timbang lot
    hanya bukti mutu (KEPUTUSAN.md K3).

    Test acuan T11 (WAJIB, K1): A 800 kg atap 415 + B 10 kg atap 27.100 @80 km
    → H_kasar 671, H_A=415, H_B=671, tagihan 338.710, subsidi 204.290.
    """
    volume_total = sum(p.volume_kg for p in partisipasi)
    rencana = rencana_armada(volume_total, jarak_km, tiers, maks_kendaraan)
    h_kasar = math.ceil(rencana.biaya_total / volume_total)

    tagihan: dict[UUID, int] = {}
    kembalian: dict[UUID, int] = {}
    for p in partisipasi:
        # Pembanding: jaminan atap (spec §5.5) — petani tidak pernah membayar
        # di atas harga yang dijanjikan saat ia bergabung.
        h_i = min(h_kasar, p.harga_atap_per_kg)
        tagihan[p.id] = p.volume_kg * h_i
        kembalian[p.id] = p.volume_kg * (p.harga_atap_per_kg - h_i)

    # Pembanding: selisih antara biaya riil armada dan total yang benar-benar
    # ditagihkan ke petani — ditanggung koperasi, ditampilkan terbuka (§5.5).
    subsidi_koperasi = rencana.biaya_total - sum(tagihan.values())

    return HasilPenetapanHarga(
        harga_final_per_kg=h_kasar,
        biaya_total=rencana.biaya_total,
        rencana=rencana,
        tagihan=tagihan,
        kembalian=kembalian,
        subsidi_koperasi=subsidi_koperasi,
    )
