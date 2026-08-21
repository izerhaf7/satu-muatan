"""Pembaca server-side Firebase Realtime Database untuk sensor telemetri."""

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import quote

import httpx

from app.config import Settings, get_settings


class FirebaseTelemetryError(RuntimeError):
    """Raised when Firebase cannot provide a valid sensor sample."""


@dataclass(frozen=True)
class TelemetriSensorRaw:
    suhu_c: float
    kelembapan_persen: float
    sensor_uptime_ms: int
    received_at: datetime


def _url_node(base_url: str, node_path: str) -> str:
    base = base_url.rstrip("/")
    path = "/".join(part for part in node_path.strip("/").split("/") if part)
    encoded_path = "/".join(quote(part, safe="") for part in path.split("/"))
    return f"{base}/{encoded_path}.json" if encoded_path else f"{base}/.json"


def baca_telemetri_firebase(
    node_path: str,
    settings: Settings | None = None,
) -> TelemetriSensorRaw:
    """Read one sensor sample from an RTDB node without persisting it."""
    konfigurasi = settings or get_settings()
    if not konfigurasi.firebase_rtdb_url:
        raise FirebaseTelemetryError("FIREBASE_RTDB_URL belum dikonfigurasi")
    if not node_path.strip():
        raise FirebaseTelemetryError("Path node sensor tidak boleh kosong")

    try:
        params = {"auth": konfigurasi.firebase_database_secret} if konfigurasi.firebase_database_secret else None
        response = httpx.get(
            _url_node(konfigurasi.firebase_rtdb_url, node_path),
            params=params,
            timeout=konfigurasi.firebase_timeout_detik,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise FirebaseTelemetryError("Pembacaan Firebase gagal") from exc

    if not isinstance(payload, dict):
        raise FirebaseTelemetryError("Payload Firebase bukan objek JSON")

    try:
        temperature = float(payload["temperature"])
        humidity = float(payload["humidity"])
        uptime_ms = int(payload["timestamp"])
    except (KeyError, TypeError, ValueError) as exc:
        raise FirebaseTelemetryError("Payload Firebase tidak memiliki format sensor yang valid") from exc

    if not (-80 <= temperature <= 100):
        raise FirebaseTelemetryError("Suhu sensor berada di luar rentang valid")
    if not 0 <= humidity <= 100:
        raise FirebaseTelemetryError("Kelembapan sensor berada di luar rentang valid")
    if uptime_ms < 0:
        raise FirebaseTelemetryError("Timestamp uptime sensor tidak valid")

    return TelemetriSensorRaw(
        suhu_c=temperature,
        kelembapan_persen=humidity,
        sensor_uptime_ms=uptime_ms,
        received_at=datetime.now(timezone.utc),
    )
