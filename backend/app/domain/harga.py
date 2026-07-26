"""Mesin harga: atap, berjalan, penetapan final, jaminan atap, cek luapan
(spec §5.3–§5.5, KEPUTUSAN.md K1/K6).

Fase 0: signature beku. Implementasi oleh agent domain-engine (Fase 1), test-first.
"""

from dataclasses import dataclass
from uuid import UUID

from app.domain.armada import RencanaArmada, Tier


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
    raise NotImplementedError


def harga_berjalan_per_kg(volume_total_kg: int, jarak_km: float, tiers: list[Tier], maks_kendaraan: int) -> int:
    """Harga per kg dengan volume terkunci saat ini. Dibulatkan ke atas (ceil)."""
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError
