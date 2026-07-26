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
    # Pembanding: baseline "tiap petani mengirim sendiri-sendiri" — konsolidasi
    # menghemat (n-1) perjalanan truk sejauh jarak yang sama.
    truk_km_dihemat = (jumlah_partisipan - 1) * jarak_km
    emisi_dihemat_kg_co2 = truk_km_dihemat * faktor_emisi

    # Pembanding: penghematan per peserta pakai H_i MILIK peserta itu (bukan
    # H_kasar global) — identik dengan Σ kembalian dari mesin harga, sehingga
    # peserta yang ter-cap jaminan atap tidak pernah menghasilkan angka negatif.
    penghematan_ongkos_rp = sum(
        p.volume_kg * (p.harga_atap_per_kg - p.harga_final_per_kg) for p in partisipasi
    )

    # Pembanding: susut dicegah HANYA berarti kalau ada data jam yang benar-benar
    # dihemat dibanding transit sendiri-sendiri; tanpa itu, None → UI "—".
    if jam_dihemat is not None and jam_dihemat > 0:
        susut_dicegah_kg = sum(
            p.volume_kg * laju_susut_per_jam[p.komoditas_id] * jam_dihemat for p in partisipasi
        )
    else:
        susut_dicegah_kg = None

    return Dampak(
        truk_km_dihemat=truk_km_dihemat,
        emisi_dihemat_kg_co2=emisi_dihemat_kg_co2,
        penghematan_ongkos_rp=penghematan_ongkos_rp,
        susut_dicegah_kg=susut_dicegah_kg,
    )
