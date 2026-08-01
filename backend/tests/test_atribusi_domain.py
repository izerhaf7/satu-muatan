"""Test domain atribusi.py — ambang transit & tabel keputusan 3-input (spec v2 §6.5).

A1–A6 wajib hijau. Cabang TIDAK_TERBUKTI wajib ada (CLAUDE.md #4) — jangan
pernah dihapus dari test.
"""

from app.domain.atribusi import ambang_transit_menit, tentukan_atribusi


def _atribusi(
    grade_asal: int,
    grade_tiba: int,
    durasi: int = 100,
    ambang: int = 181,
    sisa: int = 80,
    ambang_grade: int = 3,
    ambang_paparan: int = 50,
) -> str:
    return tentukan_atribusi(
        grade_asal=grade_asal,
        grade_tiba=grade_tiba,
        durasi_transit_menit=durasi,
        ambang_menit=ambang,
        sisa_umur_simpan_persen=sisa,
        ambang_grade_asal=ambang_grade,
        ambang_paparan_persen=ambang_paparan,
    )


# ---------------------------------------------------------------------------
# ambang_transit_menit (tidak berubah dari v1)
# ---------------------------------------------------------------------------


def test_ambang_transit_menit_jarak_80km():
    # (80/35)*60*1.5 = 205.71... → ceil = 206.
    assert ambang_transit_menit(80, 35, 1.5) == 206


def test_ambang_transit_menit_jarak_rute_demo():
    # KEPUTUSAN.md K2 — rute demo 70,03 km @35 km/j ×1,5 → 181 menit.
    assert ambang_transit_menit(70.03, 35, 1.5) == 181


def test_ambang_transit_menit_pembulatan_ke_atas():
    # (35/35)*60*1.0 = 60 tepat — hasil pas bulat tidak dibulatkan naik lagi.
    assert ambang_transit_menit(35, 35, 1.0) == 60


# ---------------------------------------------------------------------------
# tentukan_atribusi — tabel keputusan 3-input (§6.2, urutan jangan diubah)
# ---------------------------------------------------------------------------


def test_a1_grade_asal_di_bawah_ambang_selalu_petani():
    assert _atribusi(grade_asal=2, grade_tiba=5) == "PETANI"


def test_a2_tidak_ada_penurunan_normal():
    assert _atribusi(grade_asal=5, grade_tiba=5) == "NORMAL"


def test_a3_penurunan_plus_transit_lewat_ambang_logistik():
    assert _atribusi(grade_asal=5, grade_tiba=2, durasi=200, ambang=181, sisa=80) == "LOGISTIK"


def test_a4_penurunan_plus_sisa_umur_rendah_logistik():
    assert _atribusi(grade_asal=5, grade_tiba=2, durasi=100, ambang=181, sisa=30) == "LOGISTIK"


def test_a5_penurunan_tanpa_bukti_paparan_tidak_terbukti():
    # Cabang residual WAJIB ada (CLAUDE.md #4): ada penurunan, tapi transit
    # di dalam ambang DAN sisa umur masih wajar — penyebab tidak terekam.
    assert _atribusi(grade_asal=5, grade_tiba=3, durasi=178, ambang=181, sisa=71) == "TIDAK_TERBUKTI"


def test_a6_grade_tiba_lebih_baik_normal():
    assert _atribusi(grade_asal=4, grade_tiba=5) == "NORMAL"


def test_batas_durasi_sama_dengan_ambang_tidak_terbukti():
    # durasi == ambang bukan "melebihi" (>), jadi tetap TIDAK_TERBUKTI.
    assert _atribusi(grade_asal=5, grade_tiba=3, durasi=181, ambang=181, sisa=80) == "TIDAK_TERBUKTI"
