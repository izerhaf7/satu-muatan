"""Skema Berita Acara (§9.8) — halaman siap cetak via window.print().
Tanda tangan = garis kosong di halaman cetak (K4), tidak ada penyimpanan digital."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.lot import LotOut, SerahTerimaOut
from app.schemas.master import TitikKumpulOut
from app.schemas.slot import RuteSegmenOut


class OngkosPetaniOut(BaseModel):
    """Rincian ongkos per petani (§9.8) — basis volume komitmen (K3)."""

    partisipasi_id: UUID
    nama_petani: str
    nama_komoditas: str
    volume_kg: int
    harga_atap_per_kg: int
    harga_final_per_kg: int  # H_i = min(H_kasar, atap_i)
    tagihan_rp: int
    kembalian_rp: int


class LotBeritaOut(BaseModel):
    lot: LotOut
    serah_terima: SerahTerimaOut | None = None


class BeritaAcaraOut(BaseModel):
    kode_slot: str
    tanggal_kirim: date
    titik_kumpul: TitikKumpulOut
    tujuan: list[RuteSegmenOut]
    lot: list[LotBeritaOut]
    rincian_ongkos: list[OngkosPetaniOut]
    biaya_total: int | None = None
    harga_final_per_kg: int | None = None
    selisih_jaminan_atap: int  # baris "Selisih dijamin platform" (§5.5, rename v2 §2)
    dibuat_pada: datetime
