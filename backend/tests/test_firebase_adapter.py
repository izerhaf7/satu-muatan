from datetime import datetime, timezone

import httpx
import pytest

from app.adapters.telemetri.firebase import (
    FirebaseTelemetryError,
    baca_telemetri_firebase,
)
from app.config import Settings


def _settings() -> Settings:
    return Settings(
        firebase_rtdb_url="https://example.firebaseio.com",
        firebase_database_secret="test-secret",
    )


def test_baca_telemetri_firebase_memetakan_payload(monkeypatch):
    request = httpx.Request("GET", "https://example.firebaseio.com/sensor/dht.json")
    response = httpx.Response(
        200,
        json={"temperature": 28.5, "humidity": 74, "timestamp": 1234},
        request=request,
    )

    def fake_get(url, *, params, timeout):
        assert url == "https://example.firebaseio.com/sensor/dht.json"
        assert params == {"auth": "test-secret"}
        assert timeout == 5.0
        return response

    monkeypatch.setattr("app.adapters.telemetri.firebase.httpx.get", fake_get)

    hasil = baca_telemetri_firebase("/sensor/dht", _settings())

    assert hasil.suhu_c == 28.5
    assert hasil.kelembapan_persen == 74.0
    assert hasil.sensor_uptime_ms == 1234
    assert hasil.received_at.tzinfo == timezone.utc
    assert isinstance(hasil.received_at, datetime)


def test_baca_telemetri_firebase_menolak_payload_tidak_valid(monkeypatch):
    request = httpx.Request("GET", "https://example.firebaseio.com/sensor.json")
    response = httpx.Response(200, json={"temperature": 28}, request=request)
    monkeypatch.setattr("app.adapters.telemetri.firebase.httpx.get", lambda *args, **kwargs: response)

    with pytest.raises(FirebaseTelemetryError, match="format sensor"):
        baca_telemetri_firebase("sensor", _settings())


def test_baca_telemetri_firebase_mendukung_node_public(monkeypatch):
    request = httpx.Request("GET", "https://example.firebaseio.com/sensor.json")
    response = httpx.Response(
        200,
        json={"temperature": 31.1, "humidity": 50.3, "timestamp": 5073598},
        request=request,
    )
    settings = Settings(firebase_rtdb_url="https://example.firebaseio.com")

    def fake_get(url, *, params, timeout):
        assert url == "https://example.firebaseio.com/sensor.json"
        assert params is None
        return response

    monkeypatch.setattr("app.adapters.telemetri.firebase.httpx.get", fake_get)
    hasil = baca_telemetri_firebase("/sensor", settings)

    assert hasil.suhu_c == 31.1
    assert hasil.kelembapan_persen == 50.3
    assert hasil.sensor_uptime_ms == 5073598
