"""Skema lokasi pengguna untuk penugasan petugas berbasis GPS."""

from datetime import datetime

from pydantic import BaseModel, Field


class LokasiPenggunaRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class LokasiPenggunaOut(BaseModel):
    lat: float
    lng: float
    diperbarui_pada: datetime
