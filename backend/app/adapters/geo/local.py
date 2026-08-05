"""Database-backed geo provider used offline and as fallback."""

import math

from sqlalchemy.orm import Session

from app.adapters.geo.base import AddressResult, CoordinateResult, SuggestionResult
from app.models import Wilayah


def _jarak_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(min(1.0, a)))


class LocalGeoAdapter:
    def __init__(self, db: Session, max_distance_km: float):
        self.db = db
        self.max_distance_km = max_distance_km

    @staticmethod
    def _tidak_ditemukan(lat: float, lng: float) -> AddressResult:
        return AddressResult(alamat=f"Titik {lat:.4f}, {lng:.4f}", sumber="TIDAK_DITEMUKAN")

    def _hierarki(self, wilayah: Wilayah) -> dict[str, str] | None:
        tingkat_induk = {
            "DESA": "KECAMATAN",
            "KECAMATAN": "KABUPATEN",
            "KABUPATEN": "PROVINSI",
            "PROVINSI": None,
        }
        nama_per_tingkat: dict[str, str] = {}
        dikunjungi: set[str] = set()
        sekarang: Wilayah | None = wilayah
        while sekarang is not None:
            if (
                sekarang.kode in dikunjungi
                or sekarang.tingkat in nama_per_tingkat
                or sekarang.tingkat not in tingkat_induk
            ):
                return None
            dikunjungi.add(sekarang.kode)
            nama_per_tingkat[sekarang.tingkat] = sekarang.nama
            if sekarang.induk_kode is None:
                if tingkat_induk[sekarang.tingkat] is not None:
                    return None
                sekarang = None
                continue
            induk = self.db.get(Wilayah, sekarang.induk_kode)
            if induk is None or induk.tingkat != tingkat_induk[sekarang.tingkat]:
                return None
            sekarang = induk

        tingkat_wajib = {
            "DESA": {"DESA", "KECAMATAN", "KABUPATEN", "PROVINSI"},
            "KECAMATAN": {"KECAMATAN", "KABUPATEN", "PROVINSI"},
            "KABUPATEN": {"KABUPATEN", "PROVINSI"},
            "PROVINSI": {"PROVINSI"},
        }.get(wilayah.tingkat)
        if tingkat_wajib is None or not tingkat_wajib.issubset(nama_per_tingkat):
            return None
        return nama_per_tingkat

    def reverse(self, lat: float, lng: float) -> AddressResult:
        if not math.isfinite(self.max_distance_km) or self.max_distance_km < 0:
            return self._tidak_ditemukan(lat, lng)
        kandidat = self.db.query(Wilayah).filter(Wilayah.lat.isnot(None), Wilayah.lng.isnot(None)).all()
        if not kandidat:
            return self._tidak_ditemukan(lat, lng)
        terdekat = min(kandidat, key=lambda w: _jarak_km(lat, lng, w.lat, w.lng))
        jarak_km = _jarak_km(lat, lng, terdekat.lat, terdekat.lng)
        if jarak_km > self.max_distance_km:
            return self._tidak_ditemukan(lat, lng)
        hierarki = self._hierarki(terdekat)
        if hierarki is None:
            return self._tidak_ditemukan(lat, lng)
        return AddressResult(
            alamat=terdekat.jalur,
            desa=hierarki.get("DESA"),
            kecamatan=hierarki.get("KECAMATAN"),
            kabupaten=hierarki.get("KABUPATEN"),
            provinsi=hierarki.get("PROVINSI"),
            kode_pos=terdekat.kode_pos,
            jarak_meter=jarak_km * 1000,
            # Linear terhadap radius konfigurasi: 1 di centroid, 0 di batas.
            keyakinan=max(0.0, min(1.0, 1.0 - jarak_km / self.max_distance_km))
            if self.max_distance_km > 0
            else 1.0,
        )

    def autocomplete(self, query: str, limit: int = 10) -> list[SuggestionResult]:
        pola = query.strip().lower()
        rows = (
            self.db.query(Wilayah)
            .filter(Wilayah.tingkat.in_(("DESA", "KECAMATAN", "KABUPATEN")))
            .filter(Wilayah.nama.ilike(f"%{pola}%"))
            .all()
        )
        rows.sort(key=lambda w: (not w.nama.lower().startswith(pola), len(w.nama), w.nama))
        return [
            SuggestionResult(
                place_id=w.kode,
                nama=w.nama,
                alamat=w.jalur,
                lat=w.lat,
                lng=w.lng,
                sumber="LOKAL",
                tingkat=w.tingkat,
                kode_pos=w.kode_pos,
            )
            for w in rows[:limit]
        ]

    def forward(self, query: str) -> CoordinateResult | None:
        pola = query.strip().lower()
        row = (
            self.db.query(Wilayah)
            .filter(Wilayah.nama.ilike(pola), Wilayah.lat.isnot(None), Wilayah.lng.isnot(None))
            .order_by(Wilayah.nama)
            .first()
        )
        if row is None:
            row = (
                self.db.query(Wilayah)
                .filter(Wilayah.nama.ilike(f"%{pola}%"), Wilayah.lat.isnot(None), Wilayah.lng.isnot(None))
                .order_by(Wilayah.nama)
                .first()
            )
        if row is None or row.lat is None or row.lng is None:
            return None
        return CoordinateResult(row.lat, row.lng, row.jalur)
