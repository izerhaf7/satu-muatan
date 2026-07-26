"""Interface vendor logistik (spec §8.1)."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class Titik:
    lat: float
    lng: float
    label: str = ""


@dataclass(frozen=True)
class Kontak:
    nama: str
    no_hp: str


@dataclass(frozen=True)
class Kuotasi:
    kuotasi_id: str
    vendor: str
    tier_kode: str
    biaya_total: int
    rincian: dict  # respons mentah — disimpan ke pengiriman.kuotasi_json


@dataclass(frozen=True)
class Pesanan:
    vendor_ref: str
    status: str


@dataclass(frozen=True)
class StatusPengiriman:
    status: str  # DIPESAN | MENUJU_MUAT | JALAN | TIBA
    waktu_berangkat: datetime | None
    waktu_tiba: datetime | None


class VendorAdapter(Protocol):
    nama: str

    def kuotasi(self, titik: list[Titik], tier_kode: str) -> Kuotasi: ...

    def pesan(self, kuotasi_id: str, kontak: Kontak) -> Pesanan: ...

    def status(self, vendor_ref: str) -> StatusPengiriman: ...
