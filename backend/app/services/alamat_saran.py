"""Provider-neutral address suggestion and resolution orchestration."""

import base64
import hashlib
import hmac
from typing import Literal

from sqlalchemy.orm import Session

from app.adapters.geo.base import PlaceResolutionResult, SuggestionResult
from app.adapters.geo.google import GoogleGeoAdapter
from app.adapters.geo.local import LocalGeoAdapter
from app.config import get_settings
from app.models import Wilayah

PESAN_FALLBACK = "Pencarian alamat presisi sedang tidak tersedia. Pilih wilayah lokal atau tentukan titik di peta."
PESAN_TITIK = "Koordinat wilayah masih kasar. Tentukan titik tepat di peta."
PESAN_TITIK_GOOGLE = "Koordinat alamat belum presisi. Konfirmasi titik tepat di peta."
PESAN_TIDAK_DITEMUKAN = "Alamat tidak dapat diselesaikan. Cari ulang atau tentukan titik di peta."


def _token_lokal(kode: str, secret: str) -> str:
    payload = base64.urlsafe_b64encode(kode.encode()).decode().rstrip("=")
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]
    return f"lokal.{payload}.{signature}"


def _kode_lokal(token: str, secret: str) -> str | None:
    try:
        prefix, payload, signature = token.split(".")
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]
        if prefix != "lokal" or not hmac.compare_digest(signature, expected):
            return None
        padding = "=" * (-len(payload) % 4)
        return base64.urlsafe_b64decode(payload + padding).decode()
    except (ValueError, UnicodeError):
        return None


def _lokal_suggestions(db: Session, query: str, limit: int, secret: str) -> list[SuggestionResult]:
    rows = LocalGeoAdapter(db, get_settings().geo_local_max_distance_km).autocomplete(query, limit)
    return [
        SuggestionResult(
            place_id=_token_lokal(item.place_id or "", secret),
            nama=item.nama,
            alamat=item.alamat or item.nama,
            sumber="LOKAL",
            teks_sekunder=item.tingkat,
        )
        for item in rows
        if item.place_id
    ]


def saran_alamat(db: Session, query: str, bias: tuple[float, float, float] | None):
    settings = get_settings()
    limit = min(max(settings.alamat_saran_max_hasil, 1), 5)
    provider_gagal = False
    if settings.geo_provider_enabled and settings.google_maps_api_key:
        try:
            provider = GoogleGeoAdapter(
                settings.google_maps_api_key,
                timeout=settings.alamat_provider_timeout_detik,
                max_response_bytes=getattr(settings, "alamat_provider_response_max_bytes", 32_768),
            )
            hasil = provider.autocomplete(
                query,
                limit,
                bias=bias,
                max_input=200,
                max_radius=settings.alamat_bias_radius_max_meter,
            )
            if hasil:
                return hasil, "OK", None
        except Exception:
            provider_gagal = True
    lokal = _lokal_suggestions(db, query, limit, settings.jwt_secret)
    if lokal:
        return lokal, "FALLBACK_LOKAL", PESAN_FALLBACK if provider_gagal else None
    if provider_gagal:
        return [], "PENYEDIA_TIDAK_TERSEDIA", PESAN_FALLBACK
    return [], "TIDAK_DITEMUKAN", "Alamat tidak ditemukan. Coba kata lain atau tentukan titik di peta."


def resolusi_alamat(db: Session, place_id: str) -> tuple[PlaceResolutionResult | None, str, str | None]:
    settings = get_settings()
    kode_lokal = _kode_lokal(place_id, settings.jwt_secret)
    if kode_lokal is not None:
        wilayah = db.get(Wilayah, kode_lokal)
        if wilayah is None:
            return None, "TIDAK_DITEMUKAN", PESAN_TIDAK_DITEMUKAN
        hierarki = LocalGeoAdapter(db, settings.geo_local_max_distance_km)._hierarki(wilayah)
        if hierarki is None:
            return None, "TIDAK_DITEMUKAN", PESAN_TIDAK_DITEMUKAN
        granularitas_map: dict[
            str,
            Literal["DESA", "KECAMATAN", "KABUPATEN_KOTA", "PROVINSI"],
        ] = {
            "DESA": "DESA",
            "KECAMATAN": "KECAMATAN",
            "KABUPATEN": "KABUPATEN_KOTA",
            "PROVINSI": "PROVINSI",
        }
        return (
            PlaceResolutionResult(
                alamat=wilayah.jalur,
                kode_pos=wilayah.kode_pos,
                desa=hierarki.get("DESA"),
                kecamatan=hierarki.get("KECAMATAN"),
                kabupaten=hierarki.get("KABUPATEN"),
                provinsi=hierarki.get("PROVINSI"),
                granularitas=granularitas_map.get(wilayah.tingkat),
                sumber="LOKAL",
            ),
            "KOORDINAT_TIDAK_PRESISI",
            PESAN_TITIK,
        )
    if not settings.geo_provider_enabled or not settings.google_maps_api_key:
        return None, "TIDAK_DITEMUKAN", PESAN_TIDAK_DITEMUKAN
    try:
        provider = GoogleGeoAdapter(
            settings.google_maps_api_key,
            timeout=settings.alamat_provider_timeout_detik,
            max_response_bytes=getattr(settings, "alamat_provider_response_max_bytes", 32_768),
        )
        hasil = provider.resolve_place(place_id)
        if hasil.koordinat_presisi:
            return hasil, "OK", None
        return hasil, "KOORDINAT_TIDAK_PRESISI", PESAN_TITIK_GOOGLE
    except Exception:
        return None, "TIDAK_DITEMUKAN", PESAN_TIDAK_DITEMUKAN
