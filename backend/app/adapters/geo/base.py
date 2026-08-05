"""Pure contracts and immutable values for geo providers."""

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class AddressResult:
    alamat: str
    desa: str | None = None
    kecamatan: str | None = None
    kabupaten: str | None = None
    provinsi: str | None = None
    kode_pos: str | None = None
    sumber: str = "LOKAL"
    jarak_meter: float | None = None
    keyakinan: float | None = None


@dataclass(frozen=True)
class SuggestionResult:
    place_id: str | None
    nama: str
    alamat: str | None = None
    lat: float | None = None
    lng: float | None = None
    tingkat: str | None = None
    kode_pos: str | None = None
    sumber: str = "GOOGLE"
    teks_sekunder: str | None = None


@dataclass(frozen=True)
class PlaceResolutionResult:
    alamat: str
    jalan: str | None = None
    kode_pos: str | None = None
    desa: str | None = None
    kecamatan: str | None = None
    kabupaten: str | None = None
    provinsi: str | None = None
    lat: float | None = None
    lng: float | None = None
    granularitas: Literal["ALAMAT", "JALAN", "DESA", "KECAMATAN", "KABUPATEN_KOTA", "PROVINSI"] | None = None
    sumber: Literal["GOOGLE", "LOKAL"] = "GOOGLE"
    koordinat_presisi: bool = False


@dataclass(frozen=True)
class CoordinateResult:
    lat: float
    lng: float
    alamat: str | None = None
    sumber: str = "LOKAL"


@dataclass(frozen=True)
class RouteDisplayResult:
    jarak_km: float
    durasi_menit: float
    sumber: str
    polyline: str
    versi: int


class GeoProvider(Protocol):
    def reverse(self, lat: float, lng: float) -> AddressResult | None: ...

    def autocomplete(self, query: str, limit: int) -> list[SuggestionResult]: ...

    def forward(self, query: str) -> CoordinateResult | None: ...

    def route(
        self, origin: tuple[float, float], stops: list[tuple[float, float]], destination: tuple[float, float]
    ) -> RouteDisplayResult: ...
