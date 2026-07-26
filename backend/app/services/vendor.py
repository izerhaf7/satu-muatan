"""Pemilihan adapter vendor lewat env `VENDOR_ADAPTER=MOCK|DELIVEREE` (spec §8.3)."""

from sqlalchemy.orm import Session

from app.adapters.deliveree import DeliverreeAdapter
from app.adapters.mock_vendor import MockVendorAdapter
from app.config import get_settings
from app.services.konfigurasi import baca_konfigurasi, baca_tiers_aktif


def dapatkan_adapter_vendor(db: Session):
    """Factory adapter — MockVendorAdapter untuk Fase 1 (VENDOR_ADAPTER=MOCK, default demo)."""
    pengaturan = get_settings()
    if pengaturan.vendor_adapter == "DELIVEREE":
        return DeliverreeAdapter()
    tiers = baca_tiers_aktif(db)
    faktor_jalan = baca_konfigurasi(db, "faktor_jalan")
    return MockVendorAdapter(tiers=tiers, faktor_jalan=faktor_jalan)
