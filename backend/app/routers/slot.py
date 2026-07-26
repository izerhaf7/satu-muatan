"""Endpoint slot — jantung alur (§9.2–§9.4). GET /slot/{id} dipoll 3 detik."""

from uuid import UUID

from fastapi import APIRouter, Depends

from app.auth import get_pengguna_aktif, wajib_peran
from app.models.enums import StatusSlot
from app.routers import stub_fase_0
from app.schemas.slot import (
    GabungPratinjauRequest,
    GabungPratinjauResponse,
    GabungRequest,
    GabungResponse,
    LuapanKapasitasOut,
    PratinjauSlotRequest,
    PratinjauSlotResponse,
    SlotCreate,
    SlotDetailOut,
    SlotItemOut,
)

router = APIRouter(prefix="/slot", tags=["slot"])


@router.get("", response_model=list[SlotItemOut])
def daftar_slot(status: StatusSlot | None = None, pengguna=Depends(get_pengguna_aktif)):
    """Ter-scope per peran (K6): KOPERASI → miliknya; PETANI → slot koperasinya;
    PENERIMA → slot yang tujuannya memuat dirinya."""
    stub_fase_0()


@router.post("", response_model=SlotDetailOut, status_code=201)
def buka_slot(body: SlotCreate, pengguna=Depends(wajib_peran("KOPERASI"))):
    """Buka slot baru (§9.3). Server menghitung urutan drop nearest-neighbor + jarak_km."""
    stub_fase_0()


@router.post("/pratinjau", response_model=PratinjauSlotResponse)
def pratinjau_slot(body: PratinjauSlotRequest, pengguna=Depends(wajib_peran("KOPERASI"))):
    """Pratinjau §9.3: jarak rute + tabel harga/kg pada berbagai skenario volume."""
    stub_fase_0()


@router.get("/{slot_id}", response_model=SlotDetailOut)
def detail_slot(slot_id: UUID, pengguna=Depends(get_pengguna_aktif)):
    """LAYAR UTAMA DEMO (§9.4). Dipoll 3 detik — harga berjalan, partisipasi,
    rencana armada, waktu_server."""
    stub_fase_0()


@router.post(
    "/{slot_id}/gabung",
    response_model=GabungResponse,
    status_code=201,
    responses={409: {"model": LuapanKapasitasOut, "description": "LUAPAN_KAPASITAS (§5.5) — dialog dua pilihan"}},
)
def gabung_slot(slot_id: UUID, body: GabungRequest, pengguna=Depends(wajib_peran("PETANI"))):
    """'Ikut kirim' — mengunci harga_atap_per_kg petani (tidak pernah berubah)."""
    stub_fase_0()


@router.post("/{slot_id}/gabung/pratinjau", response_model=GabungPratinjauResponse)
def pratinjau_gabung(slot_id: UUID, body: GabungPratinjauRequest, pengguna=Depends(wajib_peran("PETANI"))):
    """Peringatan dini sebelum submit: atap, harga berjalan baru, potensi luapan."""
    stub_fase_0()


@router.post("/{slot_id}/tutup", response_model=SlotDetailOut)
def tutup_slot(slot_id: UUID, pengguna=Depends(wajib_peran("KOPERASI"))):
    """Cutoff (§5.4): tetapkan harga final + jaminan atap, kunci rencana armada,
    buat lot per partisipasi (alokasi penerima — K6), pesan ke vendor."""
    stub_fase_0()


@router.post("/{slot_id}/batal", response_model=SlotDetailOut)
def batal_slot(slot_id: UUID, pengguna=Depends(wajib_peran("KOPERASI"))):
    stub_fase_0()
