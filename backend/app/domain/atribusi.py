"""Mesin atribusi mutu (spec §6).

Fase 0: signature beku. Implementasi oleh agent domain-engine (Fase 1), test-first.

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
    cacat_terlihat_saat_muat: bool,
    durasi_transit_menit: int,
    ambang_menit: int,
) -> Literal["PETANI", "LOGISTIK", "TIDAK_TERBUKTI"]:
    """Tabel keputusan (spec §6 — jangan disederhanakan):

    1. cacat terlihat saat muat            → PETANI
    2. durasi transit > ambang             → LOGISTIK
    3. selain itu                          → TIDAK_TERBUKTI

    UI menampilkan PENJELASAN, bukan cuma label, mis.:
    "Tidak terbukti — tidak ada cacat di foto muat, dan waktu tempuh 178 menit
    masih di dalam ambang 181 menit untuk rute ini."
    """
    # Pembanding: cabang 1 — bukti visual langsung saat muat mengalahkan segalanya.
    if cacat_terlihat_saat_muat:
        return "PETANI"
    # Pembanding: cabang 2 — transit lebih lama dari ambang wajar rute ini.
    if durasi_transit_menit > ambang_menit:
        return "LOGISTIK"
    # Pembanding: cabang 3 — tidak ada cacat saat muat DAN transit masih wajar;
    # tidak ada bukti untuk menuding siapa pun. WAJIB ada (CLAUDE.md #4).
    return "TIDAK_TERBUKTI"
