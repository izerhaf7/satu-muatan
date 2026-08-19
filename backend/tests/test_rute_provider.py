"""Penyedia rute: haversine offline + FallbackRouteProvider Google→haversine.

Unit test `HaversineRoutesAdapter` dan `FallbackRouteProvider` murni (tanpa DB —
konfigurasi `rute_provider` di-mock lewat `unittest.mock.patch`). Satu integrasi
di akhir memakai fixture DB `data_dasar` untuk memastikan snapshot rute TANPA
kunci Google tetap berhasil (sumber "HAVERSINE") dan tidak menyentuh harga
kanonik (`slot.jarak_km`, `biaya_total`, `harga_final_per_kg`).
"""

import math
from datetime import date
from decimal import Decimal
from typing import cast
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.adapters.geo.base import RouteDisplayResult
from app.adapters.routes.google import GoogleRoutesAdapter
from app.adapters.routes.haversine import HaversineRoutesAdapter, encode_polyline
from app.domain.armada import jarak_haversine_km
from app.domain.rute_polyline import decode_polyline
from app.models import Pengiriman, Slot, SlotTujuan
from app.services.rute_provider import FallbackRouteProvider

# Titik di sekitar koridor Cikajang–Bandung (konsisten dengan conftest).
ASAL = (-7.3661, 107.7961)
JEMPUT = [(-7.1000, 107.5000), (-6.9500, 107.6500)]
TUJUAN = (-6.9269, 107.7189)

# DB tiruan untuk test yang meng-mock `baca_konfigurasi` — argumen `db` tidak
# pernah dipakai di jalur itu, jadi None aman (di-cast agar type checker tahu).
_DB_ABAIKAN: Session = cast(Session, None)


class _GoogleOK(GoogleRoutesAdapter):
    """Adapter Google tiruan yang selalu berhasil (tanpa jaringan)."""

    def __init__(self, hasil: RouteDisplayResult | None = None):
        super().__init__("kunci-tiruan")
        self._hasil = hasil or RouteDisplayResult(
            jarak_km=12.345, durasi_menit=3, sumber="GOOGLE_ROUTES", polyline="encoded-google", versi=1
        )
        self.panggilan = 0

    def route(self, origin, stops, destination):
        self.panggilan += 1
        return self._hasil


class _GoogleRusak(GoogleRoutesAdapter):
    def __init__(self):
        super().__init__("kunci-tiruan")
        self.panggilan = 0

    def route(self, origin, stops, destination):
        self.panggilan += 1
        raise OSError("provider down")


def _jarak_rantai(points: list[tuple[float, float]]) -> float:
    return sum(
        jarak_haversine_km(a[0], a[1], b[0], b[1]) for a, b in zip(points, points[1:])
    )


def _rantai() -> list[tuple[float, float]]:
    return [ASAL, *JEMPUT, TUJUAN]


# ---------------------------------------------------------------------------
# HaversineRoutesAdapter — murni, tanpa DB


def test_encode_polyline_vektor_baku_google():
    # Vektor pembanding resmi algoritma encoded polyline Google (presisi 5).
    assert (
        encode_polyline([(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)])
        == "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
    )
    with pytest.raises(ValueError):
        encode_polyline([(0.0, 0.0)], presisi=0)


def test_haversine_polyline_didekode_kembali_ke_rantai():
    hasil = HaversineRoutesAdapter().route(ASAL, JEMPUT, TUJUAN)
    assert decode_polyline(hasil.polyline) == pytest.approx(_rantai(), abs=1e-4)


def test_haversine_jarak_adalah_jumlah_haversine():
    hasil = HaversineRoutesAdapter().route(ASAL, JEMPUT, TUJUAN)
    assert hasil.jarak_km == pytest.approx(_jarak_rantai(_rantai()))


def test_haversine_durasi_default_kecepatan_35():
    hasil = HaversineRoutesAdapter().route(ASAL, JEMPUT, TUJUAN)
    jarak = _jarak_rantai(_rantai())
    assert hasil.durasi_menit == math.ceil(jarak / 35 * 60)
    assert hasil.sumber == "HAVERSINE"


def test_haversine_kecepatan_disuntikkan_pemanggil():
    hasil = HaversineRoutesAdapter(kecepatan_kmh=50.0).route(ASAL, JEMPUT, TUJUAN)
    jarak = _jarak_rantai(_rantai())
    assert hasil.durasi_menit == math.ceil(jarak / 50 * 60)


# ---------------------------------------------------------------------------
# FallbackRouteProvider — mode dari `baca_konfigurasi` (di-mock, tanpa DB)


def test_auto_jatuh_ke_haversine_saat_google_rusak():
    google = _GoogleRusak()
    provider = FallbackRouteProvider(google, HaversineRoutesAdapter())
    with patch("app.services.rute_provider.baca_konfigurasi", return_value="AUTO"):
        hasil = provider.route(_DB_ABAIKAN, ASAL, JEMPUT, TUJUAN)
    assert hasil.sumber == "HAVERSINE"
    assert hasil.polyline
    assert google.panggilan == 1


def test_auto_memakai_google_saat_google_ok():
    google = _GoogleOK()
    provider = FallbackRouteProvider(google, HaversineRoutesAdapter())
    with patch("app.services.rute_provider.baca_konfigurasi", return_value="AUTO"):
        hasil = provider.route(_DB_ABAIKAN, ASAL, JEMPUT, TUJUAN)
    assert hasil.sumber == "GOOGLE_ROUTES"
    assert hasil.jarak_km == 12.345
    assert google.panggilan == 1


def test_mode_google_memakai_google_walau_haversine_tersedia():
    google = _GoogleOK()
    provider = FallbackRouteProvider(google, HaversineRoutesAdapter())
    with patch("app.services.rute_provider.baca_konfigurasi", return_value="GOOGLE"):
        hasil = provider.route(_DB_ABAIKAN, ASAL, JEMPUT, TUJUAN)
    assert hasil.sumber == "GOOGLE_ROUTES"
    assert google.panggilan == 1


def test_mode_haversine_tidak_menyentuh_google():
    google = _GoogleOK()
    provider = FallbackRouteProvider(google, HaversineRoutesAdapter())
    with patch("app.services.rute_provider.baca_konfigurasi", return_value="HAVERSINE"):
        hasil = provider.route(_DB_ABAIKAN, ASAL, JEMPUT, TUJUAN)
    assert hasil.sumber == "HAVERSINE"
    assert google.panggilan == 0


def test_kunci_rute_provider_hilang_jatuh_ke_auto():
    google = _GoogleOK()
    provider = FallbackRouteProvider(google, HaversineRoutesAdapter())
    with patch(
        "app.services.rute_provider.baca_konfigurasi",
        side_effect=KeyError("konfigurasi 'rute_provider' tidak ditemukan"),
    ):
        hasil = provider.route(_DB_ABAIKAN, ASAL, JEMPUT, TUJUAN)
    assert hasil.sumber == "GOOGLE_ROUTES"
    assert google.panggilan == 1


def test_fallback_provider_membaca_mode_dari_db(db, data_dasar):
    # `data_dasar` me-seed `rute_provider = "AUTO"` — jalur DB nyata, tanpa mock.
    provider = FallbackRouteProvider(_GoogleRusak(), HaversineRoutesAdapter())
    hasil = provider.route(db, ASAL, JEMPUT, TUJUAN)
    assert hasil.sumber == "HAVERSINE"


# ---------------------------------------------------------------------------
# Integrasi snapshot: tanpa kunci Google, snapshot haversine tetap berhasil
# dan tidak menyentuh harga kanonik (mirror test_rute_snapshot.py).


def test_snapshot_tanpa_kunci_google_memakai_haversine_dan_tak_menyentuh_harga(db, data_dasar):
    from app.services.rute_snapshot import simpan_snapshot_rute

    tk = data_dasar["titik_kumpul"]
    penerima = data_dasar["penerima"]["cibiru"]
    slot = Slot(
        kode="SM-HAVERSINE-01",
        titik_kumpul_id=tk.id,
        tanggal_kirim=date.today(),
        cutoff_at=date.today(),
        jarak_km=Decimal("99.00"),
        biaya_total=777_000,
        harga_final_per_kg=3333,
    )
    db.add(slot)
    db.flush()
    db.add(SlotTujuan(slot_id=slot.id, penerima_id=penerima.id, urutan=1, jarak_segmen_km=Decimal("1")))
    pengiriman = Pengiriman(slot_id=slot.id, vendor="MOCK")
    db.add(pengiriman)
    db.commit()

    assert simpan_snapshot_rute(db, pengiriman, slot, enabled=True) is True
    assert pengiriman.rute_sumber == "HAVERSINE"
    assert isinstance(pengiriman.rute_polyline, str) and pengiriman.rute_polyline
    assert pengiriman.rute_versi == 1
    assert pengiriman.rute_jarak_provider_km is not None
    assert pengiriman.rute_durasi_provider_menit == math.ceil(
        float(pengiriman.rute_jarak_provider_km) / 35 * 60
    )
    # Harga kanonik TIDAK berubah — snapshot murni informasional.
    assert slot.jarak_km == Decimal("99.00")
    assert slot.biaya_total == 777_000
    assert slot.harga_final_per_kg == 3333
    # Jarak provider = jarak haversine rantai titik kumpul → penerima.
    rantai = [(tk.lat, tk.lng), (penerima.lat, penerima.lng)]
    assert float(pengiriman.rute_jarak_provider_km) == pytest.approx(_jarak_rantai(rantai))
