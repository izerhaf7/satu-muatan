"""Orkestrator penyedia rute: Google → haversine sesuai konfigurasi.

Membaca kunci `rute_provider` dari tabel `konfigurasi` dan memilih penyedia:
- "GOOGLE"    → hanya Google Routes.
- "HAVERSINE" → hanya haversine (offline).
- "AUTO"      → coba Google; kegagalan apa pun (timeout, ValueError, jaringan)
                jatuh ke haversine. Tidak pernah melempar kegagalan penyedia —
                kalau haversine pun gagal (seharusnya tidak), baru dilempar ulang.
"""

from sqlalchemy.orm import Session

from app.adapters.geo.base import RouteDisplayResult
from app.adapters.routes.google import GoogleRoutesAdapter
from app.adapters.routes.haversine import HaversineRoutesAdapter
from app.services.konfigurasi import baca_konfigurasi


class FallbackRouteProvider:
    def __init__(self, google: GoogleRoutesAdapter, haversine: HaversineRoutesAdapter):
        self._google = google
        self._haversine = haversine

    def _mode(self, db: Session) -> str:
        try:
            return str(baca_konfigurasi(db, "rute_provider")).strip().upper()
        except KeyError:
            # Kunci belum ter-seed → perilaku default AUTO.
            return "AUTO"

    def route(
        self,
        db: Session,
        origin: tuple[float, float],
        stops: list[tuple[float, float]],
        destination: tuple[float, float],
    ) -> RouteDisplayResult:
        mode = self._mode(db)
        if mode == "GOOGLE":
            return self._google.route(origin, stops, destination)
        if mode == "HAVERSINE":
            return self._haversine.route(origin, stops, destination)
        # AUTO (default): Google dulu, haversine sebagai jaring pengaman.
        try:
            return self._google.route(origin, stops, destination)
        except Exception:
            return self._haversine.route(origin, stops, destination)