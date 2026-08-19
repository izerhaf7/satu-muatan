"""Haversine route adapter — fallback offline: rantai garis lurus antar titik.

Menghasilkan `RouteDisplayResult` tanpa panggilan jaringan: jarak = jumlah
haversine antar titik berurutan, durasi = jarak / kecepatan, polyline = rantai
lurus `[origin, *stops, destination]` yang di-encode dengan algoritma encoded
polyline Google (presisi 5). Adapter tetap "dumb": kecepatan masuk lewat
konstruktor, tidak dibaca dari konfigurasi di sini.
"""

import math

from app.adapters.geo.base import RouteDisplayResult
from app.domain.armada import jarak_haversine_km


def _encode_nilai(nilai: int) -> str:
    """Encode satu delta bertanda ke potongan 5-bit encoded polyline Google.

    # Pembanding: algoritma baku Google — nilai digeser kiri 1 bit, negatif
    # dikodekan sebagai komplement dua (bit paling rendah = tanda), lalu
    # dipotong 5 bit per karakter dengan bit lanjut di bit ke-5. Kebalikan
    # dari `_baca_nilai` di `app/domain/rute_polyline.py`.
    """
    nilai = ~(nilai << 1) if nilai < 0 else nilai << 1
    potongan = []
    while nilai >= 0x20:
        potongan.append(chr((0x20 | (nilai & 0x1F)) + 63))
        nilai >>= 5
    potongan.append(chr(nilai + 63))
    return "".join(potongan)


def encode_polyline(points: list[tuple[float, float]], presisi: int = 5) -> str:
    """Encode daftar (lat, lng) ke encoded polyline Google.

    `presisi` = jumlah digit desimal koordinat (default 5 → koordinat × 1e5,
    format default Directions API). Kebalikan dari `decode_polyline` di
    `app/domain/rute_polyline.py`: delta berurutan diakumulasi menjadi
    koordinat absolut, lalu dibagi skala presisi.
    """
    if presisi <= 0:
        raise ValueError(f"presisi={presisi} tidak sah — harus bilangan bulat positif")
    skala = 10**presisi
    hasil: list[str] = []
    lat_sebelum = 0
    lng_sebelum = 0
    for lat, lng in points:
        lat_terkuantisasi = round(lat * skala)
        lng_terkuantisasi = round(lng * skala)
        hasil.append(_encode_nilai(lat_terkuantisasi - lat_sebelum))
        hasil.append(_encode_nilai(lng_terkuantisasi - lng_sebelum))
        lat_sebelum = lat_terkuantisasi
        lng_sebelum = lng_terkuantisasi
    return "".join(hasil)


class HaversineRoutesAdapter:
    """Rute garis lurus antar titik — dipakai saat Google tidak tersedia.

    Interface sama dengan `GoogleRoutesAdapter.route(origin, stops, destination)
    -> RouteDisplayResult`. `kecepatan_kmh` dipakai menghitung durasi dan
    disuntikkan oleh pemanggil (orkestrator), bukan dibaca dari konfigurasi.
    """

    def __init__(self, kecepatan_kmh: float = 35.0):
        self._kecepatan_kmh = kecepatan_kmh

    def route(
        self,
        origin: tuple[float, float],
        stops: list[tuple[float, float]],
        destination: tuple[float, float],
    ) -> RouteDisplayResult:
        rantai = [origin, *stops, destination]
        jarak = sum(
            jarak_haversine_km(a[0], a[1], b[0], b[1]) for a, b in zip(rantai, rantai[1:])
        )
        return RouteDisplayResult(
            jarak_km=jarak,
            durasi_menit=math.ceil(jarak / self._kecepatan_kmh * 60),
            sumber="HAVERSINE",
            polyline=encode_polyline(rantai),
            versi=1,
        )