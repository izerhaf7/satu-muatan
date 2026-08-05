"""Server-only Google Routes adapter for informational route snapshots."""

import json
import math
import urllib.request
from collections.abc import Callable

from app.adapters.geo.base import RouteDisplayResult


class GoogleRoutesAdapter:
    _URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
    _FIELD_MASK = "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"

    def __init__(self, api_key: str, timeout: float = 4.0, request_json: Callable | None = None):
        self._api_key = api_key
        self._timeout = timeout
        self._request_json = request_json or self._request

    def _request(self, url: str, timeout: float, headers: dict[str, str], method: str, body: bytes) -> dict:
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _waypoint(lat: float, lng: float) -> dict:
        return {"location": {"latLng": {"latitude": lat, "longitude": lng}}}

    def route(
        self,
        origin: tuple[float, float],
        stops: list[tuple[float, float]],
        destination: tuple[float, float],
    ) -> RouteDisplayResult:
        if len(stops) > 25:
            raise ValueError("Google Routes menerima maksimal 25 perhentian antara origin dan destination")
        body = {
            "origin": self._waypoint(*origin),
            "destination": self._waypoint(*destination),
            "intermediates": [self._waypoint(*titik) for titik in stops],
            "travelMode": "DRIVE",
            "optimizeWaypointOrder": False,
        }
        data = self._request_json(
            self._URL,
            self._timeout,
            {
                "X-Goog-Api-Key": self._api_key,
                "X-Goog-FieldMask": self._FIELD_MASK,
                "Content-Type": "application/json",
            },
            "POST",
            json.dumps(body).encode("utf-8"),
        )
        routes = data.get("routes") if isinstance(data, dict) else None
        if not isinstance(routes, list) or not routes or not isinstance(routes[0], dict):
            raise ValueError("Google Routes tidak mengembalikan rute")
        route = routes[0]
        polyline = route.get("polyline", {}).get("encodedPolyline") if isinstance(route.get("polyline"), dict) else None
        try:
            seconds = float(str(route.get("duration", "")).removesuffix("s"))
            meters = float(route.get("distanceMeters"))
        except (TypeError, ValueError) as exc:
            raise ValueError("Respons Google Routes memiliki jarak atau durasi tidak valid") from exc
        if not isinstance(polyline, str) or not polyline or not math.isfinite(seconds) or seconds < 0 or not math.isfinite(meters) or meters < 0:
            raise ValueError("Respons Google Routes memiliki polyline, jarak, atau durasi tidak valid")
        return RouteDisplayResult(
            jarak_km=meters / 1000,
            durasi_menit=math.ceil(seconds / 60),
            sumber="GOOGLE_ROUTES",
            polyline=polyline,
            versi=1,
        )
