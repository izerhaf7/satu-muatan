"""Sisa umur simpan — model Q10, kinetika Arrhenius disederhanakan (spec v2 §4/C1).

Menopang semboyan KEAMANAN PANGAN: telemetri suhu perjalanan diubah menjadi
"jam ekivalen pada suhu acuan", lalu sisa umur simpan dalam jam & persen.

Modul domain MURNI (aturan keras CLAUDE.md #2): tanpa import DB, tanpa I/O,
tanpa datetime.now(). Koefisien komoditas (q10, suhu_acuan_c, umur_simpan_jam)
masuk lewat parameter — dibaca dari tabel komoditas oleh pemanggil.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SampelTelemetri:
    """Satu sampel suhu/kelembapan + durasi sampel itu berlaku."""

    suhu_c: float
    kelembapan_persen: float
    menit_sejak_sebelumnya: int


@dataclass(frozen=True)
class HasilPaparan:
    jam_ekivalen: float  # waktu setara pada suhu acuan
    jam_nyata: float
    sisa_umur_simpan_jam: float
    sisa_umur_simpan_persen: int
    suhu_maks_c: float
    suhu_rata_c: float


def hitung_paparan(
    sampel: list[SampelTelemetri],
    q10: float,
    suhu_acuan_c: float,
    umur_simpan_jam: int,
) -> HasilPaparan:
    """Model Q10 (§4.2).

        f_i          = q10 ** ((suhu_i − suhu_acuan) / 10)
        jam_ekivalen = Σ ( f_i × menit_i / 60 )
        sisa         = maks(0, umur_simpan_jam − jam_ekivalen)

    Pembanding: 'jam ekivalen' = berapa lama komoditas ini SEOLAH-OLAH disimpan
    pada suhu acuan. Suhu di atas acuan mempercepat; di bawah acuan memperlambat.
    Suhu rata-rata ditimbang menit supaya sampel singkat tidak mendominasi.
    """
    if not sampel:
        # E5: tanpa sampel tidak ada paparan — umur simpan utuh.
        return HasilPaparan(
            jam_ekivalen=0.0,
            jam_nyata=0.0,
            sisa_umur_simpan_jam=float(umur_simpan_jam),
            sisa_umur_simpan_persen=100,
            suhu_maks_c=0.0,
            suhu_rata_c=0.0,
        )

    jam_ekivalen = 0.0
    jam_nyata = 0.0
    total_menit = 0
    suhu_tertimbang = 0.0
    for s in sampel:
        f = q10 ** ((s.suhu_c - suhu_acuan_c) / 10)
        jam_ekivalen += f * s.menit_sejak_sebelumnya / 60
        jam_nyata += s.menit_sejak_sebelumnya / 60
        total_menit += s.menit_sejak_sebelumnya
        suhu_tertimbang += s.suhu_c * s.menit_sejak_sebelumnya

    # Pembanding: sisa tidak pernah negatif (E4) — habis ya habis, tidak "minus umur".
    sisa = max(0.0, umur_simpan_jam - jam_ekivalen)
    sisa_persen = round(sisa / umur_simpan_jam * 100) if umur_simpan_jam > 0 else 0
    suhu_rata = suhu_tertimbang / total_menit if total_menit > 0 else 0.0
    suhu_maks = max(s.suhu_c for s in sampel)

    return HasilPaparan(
        jam_ekivalen=jam_ekivalen,
        jam_nyata=jam_nyata,
        sisa_umur_simpan_jam=sisa,
        sisa_umur_simpan_persen=sisa_persen,
        suhu_maks_c=suhu_maks,
        suhu_rata_c=suhu_rata,
    )
