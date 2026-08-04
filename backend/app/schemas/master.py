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


class AturanKirimanOut(BaseModel):
    """K14: ambang yang harus DIKETAHUI petani sebelum menekan Kirim.

    Panel Asumsi hanya boleh dibaca PETUGAS, jadi klien petani dulu tidak punya
    cara tahu batas 50 kg — tombol Kirim tetap aktif di 10 kg dan petani baru
    ditolak setelah mengirim. Nilainya tetap datang dari tabel `konfigurasi`
    (CLAUDE.md aturan #1), bukan ditanam di frontend."""

    volume_minimal_kg: int
    jarak_maks_layanan_km: float


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
