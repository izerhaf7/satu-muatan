from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StatusPermintaan


class PermintaanCreate(BaseModel):
    komoditas_id: UUID
    volume_kg: int = Field(gt=0)
    tanggal_dibutuhkan: date


class PermintaanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    penerima_id: UUID
    nama_penerima: str
    komoditas_id: UUID
    nama_komoditas: str
    volume_kg: int
    volume_terpenuhi_kg: int
    tanggal_dibutuhkan: date
    status: StatusPermintaan
    slot_id: UUID | None = None
    dibuat_pada: datetime
