"""Skema pelacakan (§9.6): timeline Dipesan → Dimuat → Jalan → Tiba."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import SumberPosisi


class PosisiOut(BaseModel):
    lat: float | None = None
    lng: float | None = None
    waktu: datetime
    sumber: SumberPosisi


class TimelineOut(BaseModel):
    dipesan: datetime | None = None  # pengiriman.dibuat_pada (K6)
    dimuat: datetime | None = None
    berangkat: datetime | None = None
    tiba: datetime | None = None


class PengirimanOut(BaseModel):
    id: UUID
    slot_id: UUID
    vendor: str
    vendor_ref: str | None = None
    status_vendor: str | None = None
    timeline: TimelineOut
    estimasi_tiba: datetime | None = None  # dari ambang_transit_menit
    ambang_transit_menit: int
    jejak: list[PosisiOut]
