"""Kalkulator dampak keberlanjutan (spec §7, KEPUTUSAN.md K6).

Fase 0: signature beku. Implementasi oleh agent domain-engine (Fase 1), test-first.
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class PartisipasiDampak:
    """Input dampak per peserta (K6 — WAJIB membawa harga final per peserta).

    harga_final_per_kg di sini adalah H_i = min(H_kasar, atap_i) milik peserta itu,
    BUKAN H_kasar global. Dengan H_kasar global, peserta yang ter-cap jaminan atap
    (skenario T11) menghasilkan penghematan NEGATIF −Rp204.800 — salah.
    """

    id: UUID
    volume_kg: int
    harga_atap_per_kg: int
    harga_final_per_kg: int
    komoditas_id: UUID


@dataclass(frozen=True)
class Dampak:
    truk_km_dihemat: float
    emisi_dihemat_kg_co2: float
    penghematan_ongkos_rp: int
    susut_dicegah_kg: float | None  # None kalau jam_dihemat tidak tersedia — UI tampil "—", BUKAN 0


def hitung_dampak(
    jumlah_partisipan: int,
    jarak_km: float,
    partisipasi: list[PartisipasiDampak],
    faktor_emisi: float,
    laju_susut_per_jam: dict[UUID, float],  # di-key komoditas_id (K6)
    jam_dihemat: float | None,
) -> Dampak:
    """Rumus & pembanding (spec §7 — wajib juga tampil di tooltip UI):

    truk_km_dihemat      = (jumlah_partisipan − 1) × jarak_km
        Pembanding: setiap petani mengirim sendiri-sendiri dengan kendaraannya
        masing-masing.

    emisi_dihemat_kg_co2 = truk_km_dihemat × faktor_emisi_kg_co2_per_km

    penghematan_ongkos_rp = Σ volume_i × (harga_atap_i − harga_final_i)
        harga_final_i per PESERTA (= min(H_kasar, atap_i)) → identik dengan
        Σ kembalian_i, tidak pernah negatif (invarian K6).

    susut_dicegah_kg     = Σ volume_i × laju_susut_i × jam_dihemat
        HANYA dihitung kalau jam_dihemat tersedia dan > 0. Kalau tidak ada data,
        kembalikan None — UI menampilkan "—", JANGAN angka nol yang terlihat
        seperti hasil perhitungan. Sumber jam_dihemat: kunci konfigurasi
        `jam_dihemat_per_kirim` (K6).

    Angka berbasis koefisien ASUMSI diberi penanda visual berbeda dari
    TERVERIFIKASI di Dashboard Dampak (spec §7).
    """
    raise NotImplementedError
