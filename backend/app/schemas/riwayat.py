"""Skema riwayat partisipasi petani (layar Riwayat, aktor §2.5)."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import StatusPartisipasi


class PartisipasiRiwayatOut(BaseModel):
    id: UUID
    slot_id: UUID
    slot_kode: str
    tanggal_kirim: date
    nama_komoditas: str
    volume_kg: int
    harga_atap_per_kg: int
    harga_final_per_kg: int | None = None
    kembalian_rp: int
    status: StatusPartisipasi
