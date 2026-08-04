"""Reverse geocoding: koordinat → alamat (K14).

Tiga lapis, sengaja diurutkan dari yang paling akurat ke yang paling tahan
banting:

1. **Cache database.** Koordinat dibulatkan jadi kunci, jadi titik demo yang
   sama tidak pernah memanggil jaringan dua kali.
2. **Google Geocoding API**, hanya kalau `GOOGLE_MAPS_API_KEY` diisi di env.
   Panggilannya dari SERVER — kunci API tidak pernah masuk browser.
3. **Wilayah terdekat dari tabel `wilayah` kita sendiri.** Selalu tersedia,
   tanpa kunci, tanpa internet.

Lapis 3 itulah yang membuat demo tidak pernah mati: kalau juri membukanya di
jaringan yang buruk, atau kuota Google habis, alamatnya tetap terisi — hanya
kurang presisi, dan itu dinyatakan apa adanya lewat `sumber`.

Nominatim (OpenStreetMap) sengaja TIDAK dipakai sebagai tulang punggung:
kebijakan resminya membatasi 1 permintaan/detik dan secara eksplisit melarang
aplikasi pelacakan kendaraan, sementara cakupan alamat OSM di Indonesia tipis.
"""

import json
import math
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import GeokodeCache, Wilayah

# Pembulatan kunci cache: 4 desimal ≈ 11 meter — cukup halus untuk membedakan
# dua bangunan, cukup kasar untuk membuat ketukan berulang mengenai cache.
_DESIMAL_KUNCI = 4
_TIMEOUT_DETIK = 6


@dataclass(frozen=True)
class HasilGeokode:
    alamat: str
    desa: str | None = None
    kecamatan: str | None = None
    kabupaten: str | None = None
    provinsi: str | None = None
    kode_pos: str | None = None
    sumber: str = "LOKAL"  # GOOGLE | LOKAL


def _kunci(lat: float, lng: float) -> str:
    return f"{round(lat, _DESIMAL_KUNCI)},{round(lng, _DESIMAL_KUNCI)}"


def _jarak_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(min(1.0, a)))


def _dari_google(lat: float, lng: float, kunci_api: str) -> HasilGeokode | None:
    """Panggil Google Geocoding API. Kegagalan apa pun -> None, biar jatuh ke lokal."""
    parameter = urllib.parse.urlencode({"latlng": f"{lat},{lng}", "key": kunci_api, "language": "id"})
    url = f"https://maps.googleapis.com/maps/api/geocode/json?{parameter}"
    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT_DETIK) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        # Jaringan mati, kuota habis, kunci salah — semuanya berakhir sama:
        # pakai data lokal. Demo tidak boleh berhenti karena layanan luar.
        return None

    if data.get("status") != "OK" or not data.get("results"):
        return None

    hasil = data["results"][0]
    bagian = {}
    for komponen in hasil.get("address_components", []):
        for tipe in komponen.get("types", []):
            bagian[tipe] = komponen.get("long_name")

    return HasilGeokode(
        alamat=hasil.get("formatted_address", ""),
        desa=bagian.get("administrative_area_level_4") or bagian.get("sublocality_level_1"),
        kecamatan=bagian.get("administrative_area_level_3"),
        kabupaten=bagian.get("administrative_area_level_2"),
        provinsi=bagian.get("administrative_area_level_1"),
        kode_pos=bagian.get("postal_code"),
        sumber="GOOGLE",
    )


def _dari_lokal(db: Session, lat: float, lng: float) -> HasilGeokode:
    """Wilayah berkoordinat yang paling dekat dari tabel kita sendiri.

    Hanya sebagian wilayah yang punya koordinat (sumber resmi tidak
    menyertakannya), jadi hasilnya bisa jadi kecamatan tetangga. Itu tetap jauh
    lebih berguna daripada menampilkan angka lintang-bujur telanjang kepada
    petani — dan `sumber` menyatakan tingkat kepastiannya apa adanya."""
    kandidat = db.query(Wilayah).filter(Wilayah.lat.isnot(None), Wilayah.lng.isnot(None)).all()
    if not kandidat:
        return HasilGeokode(alamat=f"Titik {lat:.4f}, {lng:.4f}", sumber="LOKAL")

    terdekat = min(kandidat, key=lambda w: _jarak_km(lat, lng, w.lat, w.lng))
    bagian = [b.strip() for b in terdekat.jalur.split(",")]
    return HasilGeokode(
        alamat=terdekat.jalur,
        kecamatan=bagian[0] if len(bagian) > 0 else None,
        kabupaten=bagian[1] if len(bagian) > 1 else None,
        provinsi=bagian[2] if len(bagian) > 2 else None,
        kode_pos=terdekat.kode_pos,
        sumber="LOKAL",
    )


def geokode_balik(db: Session, lat: float, lng: float) -> HasilGeokode:
    kunci = _kunci(lat, lng)
    tersimpan = db.get(GeokodeCache, kunci)
    if tersimpan is not None:
        return HasilGeokode(**json.loads(tersimpan.hasil_json))

    kunci_api = get_settings().google_maps_api_key
    hasil = _dari_google(lat, lng, kunci_api) if kunci_api else None
    if hasil is None:
        hasil = _dari_lokal(db, lat, lng)

    db.add(GeokodeCache(kunci=kunci, sumber=hasil.sumber, hasil_json=json.dumps(asdict(hasil))))
    db.commit()
    return hasil
