"""Gerak sepanjang rute jalan dari encoded polyline Google (spec §5.4, Lacak).

Fungsi-fungsi di modul ini MURNI: tidak ada I/O, DB, maupun clock. Satu-satunya
ketergantungan adalah `jarak_haversine_km` dari `armada.py` — jarak sepanjang
polyline di sini adalah kilometer RIIL (haversine), bukan estimasi harga yang
dikalikan faktor_jalan.
"""

from app.domain.armada import jarak_haversine_km

# Pembatas aman decoder — disalin dari frontend `geometriRute.ts`.
_BATAS_KARAKTER = 100_000
_BATAS_TITIK = 10_000
_GESER_MAKS = 30  # maksimal 6 potongan 5-bit per nilai — aman untuk int 32-bit


def _baca_nilai(encoded: str, indeks_awal: int) -> tuple[int, int] | None:
    """Baca satu nilai delta ter-encode polyline mulai `indeks_awal`.

    Mengembalikan (nilai_bertanda, indeks_setelah_nilai) atau None kalau
    input rusak (kode karakter di luar rentang atau nilai tak pernah selesai).

    # Pembanding: algoritma encoded polyline Google — 5-bit per potongan, bit
    # tinggi menandakan lanjut, nilai negatif dikodekan sebagai komplement dua
    # (bit paling rendah = tanda). Sama persis dengan `bacaNilai` di frontend.
    """
    hasil = 0
    geser = 0
    indeks = indeks_awal

    while indeks < len(encoded) and geser <= _GESER_MAKS:
        kode = ord(encoded[indeks]) - 63
        if kode < 0 or kode > 63:
            return None
        indeks += 1
        hasil |= (kode & 0x1F) << geser
        if kode < 0x20:
            # bit lanjut bersih → nilai selesai; pulihkan tanda.
            if hasil & 1:
                return ~(hasil >> 1), indeks
            return hasil >> 1, indeks
        geser += 5

    return None


def decode_polyline(encoded: str, presisi: int = 5) -> list[tuple[float, float]]:
    """Dekode encoded polyline Google ke daftar (lat, lng) dalam derajat.

    `presisi` = jumlah digit desimal koordinat (default 5 → koordinat × 1e5,
    format default Directions API). Mengangkat `ValueError` kalau input rusak:
    kode karakter di luar rentang, hasil kosong, atau kurang dari dua titik —
    sama dengan kontrak `decodePolyline` frontend yang menolak rute tak valid.

    # Pembanding: delta berurutan diakumulasi menjadi koordinat absolut, lalu
    # dibagi skala presisi — port langsung dari `decodePolyline` di
    # `frontend/src/utils/geometriRute.ts` (benteng keamanan & batas titik
    # dipertahankan).
    """
    if presisi <= 0:
        raise ValueError(f"presisi={presisi} tidak sah — harus bilangan bulat positif")
    if not encoded:
        raise ValueError("encoded polyline kosong")
    if len(encoded) > _BATAS_KARAKTER:
        raise ValueError(f"encoded polyline melebihi {_BATAS_KARAKTER} karakter")

    skala = 10**presisi
    titik: list[tuple[float, float]] = []
    indeks = 0
    lat = 0
    lng = 0

    while indeks < len(encoded):
        delta_lat = _baca_nilai(encoded, indeks)
        if delta_lat is None:
            raise ValueError(f"encoded polyline rusak pada indeks {indeks}")
        delta_lng = _baca_nilai(encoded, delta_lat[1])
        if delta_lng is None:
            raise ValueError(f"encoded polyline rusak pada indeks {delta_lat[1]}")

        lat += delta_lat[0]
        lng += delta_lng[0]
        indeks = delta_lng[1]

        koordinat = (lat / skala, lng / skala)
        if not (-90.0 <= koordinat[0] <= 90.0 and -180.0 <= koordinat[1] <= 180.0):
            raise ValueError(f"koordinat di luar rentang sah pada indeks {indeks}: {koordinat}")
        if len(titik) >= _BATAS_TITIK:
            raise ValueError(f"polyline melebihi {_BATAS_TITIK} titik")
        titik.append(koordinat)

    if len(titik) < 2:
        raise ValueError("polyline harus memiliki setidaknya dua titik")
    return titik


def panjang_polyline_km(polyline: list[tuple[float, float]]) -> float:
    """Total panjang polyline dalam km = Σ `jarak_haversine_km` antar titik.

    Kurang dari dua titik → 0.0 (polyline degenerat dianggap tak punya panjang).

    # Pembanding: di sini jarak TIDAK dikalikan faktor_jalan — jarak ini
    # dipakai gerak simulasi (Lacak), harus kilometer riil, bukan estimasi
    # dasar harga.
    """
    total = 0.0
    for (lat1, lng1), (lat2, lng2) in zip(polyline, polyline[1:]):
        total += jarak_haversine_km(lat1, lng1, lat2, lng2)
    return total


def posisi_pada_polyline(
    polyline: list[tuple[float, float]],
    jarak_tempuh_km: float,
) -> tuple[float, float]:
    """Posisi (lat, lng) setelah menempuh `jarak_tempuh_km` km dari awal polyline.

    Berjalan per segmen dengan jarak haversine kumulatif, lalu interpolasi
    linear di dalam segmen yang memuat jarak tersebut. Klamp di kedua ujung:
    `jarak_tempuh_km <= 0` → titik pertama; `jarak_tempuh_km >= panjang total`
    → titik terakhir.

    Polyline SATU titik → mengembalikan titik itu (tak ada arah untuk
    berjalan). Polyline KOSONG → `ValueError`: tidak ada titik yang bisa
    dijadikan posisi.

    # Pembanding: posisi dihitung dari jarak yang DITEMPUH, bukan proporsi
    # terhadap panjang total — kalau panjang segmen tak seragam, interpolasi
    # global akan menaruh posisi di segmen yang salah (lihat test
    # `test_posisi_mendarat_di_segmen_yang_benar`).
    """
    if not polyline:
        raise ValueError("polyline kosong — tidak ada titik untuk dijadikan posisi")
    if len(polyline) < 2 or jarak_tempuh_km <= 0:
        return polyline[0]

    total = panjang_polyline_km(polyline)
    if jarak_tempuh_km >= total:
        return polyline[-1]

    kumulatif = 0.0
    for (lat1, lng1), (lat2, lng2) in zip(polyline, polyline[1:]):
        panjang_segmen = jarak_haversine_km(lat1, lng1, lat2, lng2)
        if jarak_tempuh_km <= kumulatif + panjang_segmen:
            # Segmen dengan panjang nol (dua titik identik) → tetap di titik itu.
            fraksi = 0.0 if panjang_segmen == 0 else (jarak_tempuh_km - kumulatif) / panjang_segmen
            return (lat1 + (lat2 - lat1) * fraksi, lng1 + (lng2 - lng1) * fraksi)
        kumulatif += panjang_segmen

    # Tak terjangkau: `jarak_tempuh_km < total` dijamin di atas.
    return polyline[-1]
