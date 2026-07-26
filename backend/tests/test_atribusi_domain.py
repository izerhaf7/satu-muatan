"""Test domain atribusi.py — ambang transit & tabel keputusan atribusi mutu.

Acuan: spec §6, KEPUTUSAN.md K2 (ambang rute demo). Cabang TIDAK_TERBUKTI wajib
ada (CLAUDE.md #4) — jangan pernah dihapus dari test.
"""

from app.domain.atribusi import ambang_transit_menit, tentukan_atribusi


# ---------------------------------------------------------------------------
# ambang_transit_menit
# ---------------------------------------------------------------------------


def test_ambang_transit_menit_jarak_80km():
    # Pembanding: ceil((jarak/kecepatan)*60*faktor_toleransi), spec §6.
    # (80/35)*60*1.5 = 205.71... → ceil = 206.
    assert ambang_transit_menit(80, 35, 1.5) == 206


def test_ambang_transit_menit_jarak_rute_demo():
    # Pembanding: KEPUTUSAN.md K2 — rute demo 70,03 km @35 km/j ×1,5 → 181 menit.
    assert ambang_transit_menit(70.03, 35, 1.5) == 181


def test_ambang_transit_menit_pembulatan_ke_atas():
    # Pembanding: hasil pas bulat tidak boleh dibulatkan naik lagi (ceil dari
    # bilangan bulat = bilangan itu sendiri). (35/35)*60*1.0 = 60 tepat.
    assert ambang_transit_menit(35, 35, 1.0) == 60


# ---------------------------------------------------------------------------
# tentukan_atribusi — tabel keputusan spec §6 (jangan disederhanakan)
# ---------------------------------------------------------------------------


def test_tentukan_atribusi_cacat_terlihat_saat_muat_selalu_petani():
    # Pembanding: cabang 1 — cacat terlihat saat muat → PETANI, apa pun durasinya.
    assert tentukan_atribusi(True, durasi_transit_menit=50, ambang_menit=206) == "PETANI"


def test_tentukan_atribusi_durasi_melebihi_ambang_logistik():
    # Pembanding: cabang 2 — tanpa cacat saat muat, tapi transit lebih lama dari
    # ambang → LOGISTIK.
    assert tentukan_atribusi(False, durasi_transit_menit=207, ambang_menit=206) == "LOGISTIK"


def test_tentukan_atribusi_dalam_ambang_tidak_terbukti():
    # Pembanding: cabang 3 — tidak ada cacat, durasi masih dalam ambang →
    # TIDAK_TERBUKTI. Cabang ini WAJIB ada (CLAUDE.md #4) — sistem yang selalu
    # bisa menunjuk pihak bersalah sedang berbohong.
    assert tentukan_atribusi(False, durasi_transit_menit=178, ambang_menit=206) == "TIDAK_TERBUKTI"


def test_tentukan_atribusi_batas_durasi_sama_dengan_ambang_tidak_terbukti():
    # Pembanding: durasi == ambang bukan "melebihi" (>), jadi harus tetap
    # TIDAK_TERBUKTI, bukan LOGISTIK. Batas persis ini sering salah diimplementasikan
    # sebagai >= alih-alih >.
    assert tentukan_atribusi(False, durasi_transit_menit=206, ambang_menit=206) == "TIDAK_TERBUKTI"
