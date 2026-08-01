"""Mesin atribusi mutu — logika 3-input (spec v2 §6/C3).

ATURAN YANG TIDAK BOLEH DIUBAH (CLAUDE.md #4): cabang TIDAK_TERBUKTI wajib ada
dan wajib ditampilkan di UI apa adanya. Sistem yang selalu bisa menunjuk pihak
bersalah sedang berbohong — jawaban jujur justru menaikkan nilai di mata juri.
"""

import math
from typing import Literal


def ambang_transit_menit(jarak_km: float, kecepatan_kmh: int, faktor_toleransi: float) -> int:
    """ceil((jarak_km / kecepatan_kmh) * 60 * faktor_toleransi)

    Koefisien dari tabel `konfigurasi` (kecepatan_rata_kmh, faktor_toleransi_transit).
    Acuan rute demo 70,03 km @35 km/j ×1,5 → 181 menit (KEPUTUSAN.md K2).
    """
    # Pembanding: waktu tempuh wajar (jarak/kecepatan × 60 menit) dikali faktor
    # toleransi, dibulatkan ke atas — ambang harus longgar, bukan ketat.
    return math.ceil((jarak_km / kecepatan_kmh) * 60 * faktor_toleransi)


def tentukan_atribusi(
    grade_asal: int,
    grade_tiba: int,
    durasi_transit_menit: int,
    ambang_menit: int,
    sisa_umur_simpan_persen: int,
    ambang_grade_asal: int,
    ambang_paparan_persen: int,
) -> Literal["PETANI", "LOGISTIK", "TIDAK_TERBUKTI", "NORMAL"]:
    """Tabel keputusan 3-input (spec v2 §6.2 — urutan JANGAN diubah):

    1. grade_asal < ambang_grade_asal   → PETANI. Sudah di bawah standar sebelum berangkat.
    2. grade_tiba >= grade_asal         → NORMAL. Tidak ada penurunan; tidak perlu atribusi.
    3. Penurunan + bukti paparan berlebih:
         durasi_transit > ambang ATAU sisa_umur_simpan < ambang_paparan → LOGISTIK.
    4. Selain itu                       → TIDAK_TERBUKTI (residual model — WAJIB ada).

    UI menampilkan PENJELASAN kalimat, bukan cuma label (§6.3).
    """
    # Pembanding: cabang 1 — mutu awal di bawah standar mengalahkan segalanya.
    if grade_asal < ambang_grade_asal:
        return "PETANI"
    # Pembanding: cabang 2 — tidak ada penurunan, tidak ada yang perlu diatribusi.
    if grade_tiba >= grade_asal:
        return "NORMAL"
    # Pembanding: cabang 3 — ada penurunan DAN ada bukti paparan berlebih
    # (waktu melewati ambang rute, atau umur simpan terkikis berlebih).
    if durasi_transit_menit > ambang_menit or sisa_umur_simpan_persen < ambang_paparan_persen:
        return "LOGISTIK"
    # Pembanding: cabang 4 — ada penurunan yang tidak dijelaskan data terpantau.
    # WAJIB ada (CLAUDE.md #4): residual jujur, bukan paksa menuding pihak mana pun.
    return "TIDAK_TERBUKTI"
