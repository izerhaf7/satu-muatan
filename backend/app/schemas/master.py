from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import StatusSumber, TipePenerima, TipeTitikKumpul


class KomoditasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nama: str
    satuan: str
    harga_acuan_per_kg: int
    umur_simpan_jam: int
    laju_susut_per_jam: float
    q10: float
    suhu_acuan_c: float
    status_sumber: StatusSumber
    catatan_sumber: str | None = None


class PenerimaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nama: str
    tipe: TipePenerima
    alamat: str
    lat: float
    lng: float


class TitikKumpulOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    nama: str
    kode: str | None = None
    tipe: TipeTitikKumpul
    petugas_id: UUID | None = None
    desa: str | None = None
    kecamatan: str | None = None
    kabupaten: str | None = None
    alamat: str
    lat: float
    lng: float
