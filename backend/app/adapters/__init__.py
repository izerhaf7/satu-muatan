"""Vendor logistik lewat pola adapter (spec §8).

Pemilihan adapter lewat env `VENDOR_ADAPTER=MOCK|DELIVEREE` (app/config.py).
"""

from app.adapters.base import Kontak, Kuotasi, Pesanan, StatusPengiriman, Titik, VendorAdapter
from app.adapters.deliveree import DeliverreeAdapter
from app.adapters.mock_vendor import MockVendorAdapter


def get_vendor_adapter(nama: str) -> VendorAdapter:
    """Factory: MOCK untuk demo, DELIVEREE kalau kredensial produksi tersedia."""
    if nama.upper() == "DELIVEREE":
        return DeliverreeAdapter()
    return MockVendorAdapter()


__all__ = [
    "DeliverreeAdapter",
    "Kontak",
    "Kuotasi",
    "MockVendorAdapter",
    "Pesanan",
    "StatusPengiriman",
    "Titik",
    "VendorAdapter",
    "get_vendor_adapter",
]
