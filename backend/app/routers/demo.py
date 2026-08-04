"""Reset skenario demo (§11.2) + jalan pintas demo pelacakan (K13) —
hanya aktif saat DEMO_MODE."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import wajib_peran
from app.config import get_settings
from app.database import get_db
from app.models import Lot, Partisipasi, Pengiriman, Slot
from app.models.enums import StatusSlot
from app.routers.lot import selesai_muat
from app.routers.slot import terima_tugas, tutup_slot
from app.services.foto_contoh import FOTO_PLACEHOLDER_DEMO
from app.services.otorisasi import pastikan_petugas_muatan
from seed.skenario_demo import reset_ke_awal_demo

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoResetOut(BaseModel):
    pesan: str


class DemoBerangkatOut(BaseModel):
    slot_id: UUID
    status: str
    pengiriman_id: UUID | None = None
    resi: list[str]
    pesan: str


@router.post("/reset", response_model=DemoResetOut)
def reset_demo(db: Session = Depends(get_db)):
    """Kembalikan database ke keadaan awal skenario demo (§11.2). Idempoten,
    deterministik — memanggil fungsi bersama `reset_ke_awal_demo` (Fase 3,
    `backend/seed/skenario_demo.py`) supaya CLI (`python seed/skenario_demo.py`)
    dan endpoint ini TIDAK PERNAH berbeda perilaku.

    Data transaksional dikosongkan KECUALI 8 slot riwayat SELESAI (spec §11.1 —
    sumber grafik Dashboard Dampak); master (koperasi, penerima, komoditas,
    pengguna) + tier tetap utuh; konfigurasi dikembalikan ke nilai default seed.
    """
    if not get_settings().demo_mode:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Mode demo tidak aktif")

    reset_ke_awal_demo(db)

    return DemoResetOut(
        pesan="Data direset ke keadaan awal skenario demo (riwayat + konfigurasi default dipertahankan)."
    )


@router.post("/muatan/{slot_id}/berangkatkan", response_model=DemoBerangkatOut)
def berangkatkan_demo(
    slot_id: UUID, pengguna=Depends(wajib_peran("PETUGAS")), db: Session = Depends(get_db)
):
    """K13 (tambahan demo): SATU tombol — tutup muatan → terbitkan resi → timbang
    otomatis → berangkat, supaya pelacakan bisa langsung didemokan tanpa mengetik
    berat & foto satu per satu di depan juri.

    Sengaja memanggil ulang handler sungguhan (`tutup_slot`, `selesai_muat`)
    supaya jalan pintas ini TIDAK PERNAH menyimpang dari alur asli — kalau alur
    aslinya berubah, jalan pintas ini ikut berubah dengan sendirinya.
    """
    if not get_settings().demo_mode:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Mode demo tidak aktif")

    slot = db.get(Slot, slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Muatan tidak ditemukan")

    # K14: muatan lahir tanpa driver. Di mode demo, menekan tombol ini berarti
    # "saya yang bawa" — ambil tugasnya lebih dulu lewat handler sungguhan
    # supaya batas satu-muatan-aktif tetap ditegakkan, bukan diakali.
    if slot.petugas_id is None:
        terima_tugas(slot_id, pengguna=pengguna, db=db)
        db.refresh(slot)
    pastikan_petugas_muatan(pengguna, slot)

    if slot.status == StatusSlot.DIBUKA:
        tutup_slot(slot_id, pengguna=pengguna, db=db)
        db.refresh(slot)

    if slot.status in (StatusSlot.TERKUNCI, StatusSlot.DIMUAT):
        # Timbang otomatis: berat = volume komitmen, grade optimis. Petugas tetap
        # bisa menimbang manual lewat layar Muat kalau mau mendemokan bagian itu.
        partisipasi_ids = [p.id for p in slot.partisipasi]
        lots = db.query(Lot).filter(Lot.partisipasi_id.in_(partisipasi_ids)).all() if partisipasi_ids else []
        from datetime import datetime, timezone

        for lot in lots:
            if lot.waktu_muat is None:
                partisipasi = db.get(Partisipasi, lot.partisipasi_id)
                lot.berat_aktual_kg = partisipasi.volume_kg if partisipasi else 0
                lot.waktu_muat = datetime.now(timezone.utc)
                # K14: foto muat wajib. Jalan pintas demo tidak lewat kamera,
                # jadi diisi gambar pengganti yang jelas-jelas bukan foto asli.
                if not lot.foto_muat:
                    lot.foto_muat = FOTO_PLACEHOLDER_DEMO
        slot.status = StatusSlot.DIMUAT
        db.commit()
        selesai_muat(slot_id, pengguna=pengguna, db=db)
        db.refresh(slot)

    pengiriman = db.query(Pengiriman).filter_by(slot_id=slot.id).one_or_none()
    partisipasi_ids = [p.id for p in slot.partisipasi]
    resi = [
        lot.kode_qr
        for lot in (db.query(Lot).filter(Lot.partisipasi_id.in_(partisipasi_ids)).all() if partisipasi_ids else [])
    ]
    return DemoBerangkatOut(
        slot_id=slot.id,
        status=slot.status.value,
        pengiriman_id=pengiriman.id if pengiriman else None,
        resi=sorted(resi),
        pesan=f"Muatan berangkat. {len(resi)} nomor resi terbit dan siap dilacak.",
    )
