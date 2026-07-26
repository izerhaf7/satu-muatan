"""Endpoint lot: muat (§9.5), bukti QR & serah terima (§9.7)."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.auth import get_pengguna_aktif, wajib_peran
from app.routers import stub_fase_0
from app.schemas.lot import BuktiLotOut, LotOut, MuatPatchRequest, SerahTerimaCreate, SerahTerimaOut

router = APIRouter(tags=["lot"])


@router.get("/slot/{slot_id}/lot", response_model=list[LotOut])
def daftar_lot_slot(slot_id: UUID, pengguna=Depends(get_pengguna_aktif)):
    """Daftar lot sebuah slot — layar Muat (§9.5)."""
    stub_fase_0()


@router.patch("/lot/{lot_id}/muat", response_model=LotOut)
def muat_lot(lot_id: UUID, body: MuatPatchRequest, pengguna=Depends(wajib_peran("KOPERASI"))):
    """Timbang + foto + checkbox 'Ada cacat terlihat' (input kunci atribusi §6)."""
    stub_fase_0()


@router.post("/slot/{slot_id}/selesai-muat", response_model=list[LotOut])
def selesai_muat(slot_id: UUID, pengguna=Depends(wajib_peran("KOPERASI"))):
    """Selesai muat → slot JALAN, waktu berangkat tercatat (§9.5)."""
    stub_fase_0()


@router.get("/lot/masuk", response_model=list[BuktiLotOut])
def lot_masuk(pengguna=Depends(wajib_peran("PENERIMA"))):
    """'Pilih dari daftar' (§9.7, K6): lot menuju penerima login yang belum
    diserahterimakan — jalur demo teraman."""
    stub_fase_0()


@router.get("/lot/qr/{kode_qr}", response_model=BuktiLotOut)
def bukti_lot(kode_qr: str, pengguna=Depends(wajib_peran("PENERIMA"))):
    """Bukti lot dari scan QR: foto muat, berat, waktu, transit berjalan vs ambang."""
    stub_fase_0()


@router.post("/lot/{lot_id}/serah-terima", response_model=SerahTerimaOut, status_code=201)
def serah_terima(lot_id: UUID, body: SerahTerimaCreate, pengguna=Depends(wajib_peran("PENERIMA"))):
    """Terima / Terima dengan potongan / Tolak → atribusi + PENJELASAN (§6, §9.7)."""
    stub_fase_0()
