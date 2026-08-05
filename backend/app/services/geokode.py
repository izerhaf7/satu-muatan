"""Geo provider orchestration with cache and local fallback."""

import json
from dataclasses import asdict

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.geo.base import AddressResult
from app.adapters.geo.google import GoogleGeoAdapter
from app.adapters.geo.local import LocalGeoAdapter
from app.config import get_settings
from app.models import GeokodeCache

HasilGeokode = AddressResult
_DESIMAL_KUNCI = 4
_VERSI_CACHE = "reverse-v3"


def _kunci(lat: float, lng: float, provider: str) -> str:
    koordinat = f"{round(lat, _DESIMAL_KUNCI)},{round(lng, _DESIMAL_KUNCI)}"
    return f"{_VERSI_CACHE}:{provider}:{koordinat}"


def _google_provider(settings) -> GoogleGeoAdapter | None:
    if not settings.geo_provider_enabled or not settings.google_maps_api_key:
        return None
    return GoogleGeoAdapter(settings.google_maps_api_key)


def geokode_balik(db: Session, lat: float, lng: float) -> HasilGeokode:
    settings = get_settings()
    hasil = None
    google_dicoba = bool(settings.geo_provider_enabled and settings.google_maps_api_key)
    provider = None
    if google_dicoba:
        try:
            provider = _google_provider(settings)
        except Exception:
            provider = None
    provider_cache = "google-v1" if google_dicoba else "lokal-v2"
    kunci = _kunci(lat, lng, provider_cache)
    tersimpan = db.get(GeokodeCache, kunci)
    if tersimpan is not None:
        return HasilGeokode(**json.loads(tersimpan.hasil_json))

    lokal = LocalGeoAdapter(db, settings.geo_local_max_distance_km)
    if provider is not None:
        try:
            hasil = provider.reverse(lat, lng)
        except Exception:
            hasil = None
    if hasil is None:
        hasil = lokal.reverse(lat, lng)

    if not google_dicoba or hasil.sumber == "GOOGLE":
        db.add(GeokodeCache(kunci=kunci, sumber=hasil.sumber, hasil_json=json.dumps(asdict(hasil))))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            pemenang = db.get(GeokodeCache, kunci)
            if pemenang is None:
                raise
            return HasilGeokode(**json.loads(pemenang.hasil_json))
    return hasil
