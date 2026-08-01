"""Cek kepemilikan/visibilitas per peran (spec §12: tiga peran, cek sederhana — K6 scoping)."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Slot, SlotTujuan
from app.models.enums import PeranPengguna, StatusSlot


def slot_terlihat_oleh(pengguna, slot: Slot) -> bool:
    if pengguna.peran in (PeranPengguna.PETUGAS, PeranPengguna.PETANI):
        return slot.titik_kumpul_id == pengguna.titik_kumpul_id
    if pengguna.peran == PeranPengguna.PENERIMA:
        return any(t.penerima_id == pengguna.penerima_id for t in slot.tujuan)
    return False


def pastikan_bisa_lihat_slot(pengguna, slot: Slot) -> None:
    if not slot_terlihat_oleh(pengguna, slot):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Slot tidak dapat diakses oleh peran ini")


def query_slot_untuk_peran(db: Session, pengguna, status_filter: StatusSlot | None = None):
    """GET /api/slot — ter-scope per peran (K6):
    PETUGAS -> miliknya; PETANI -> slot titik kumpulnya; PENERIMA -> slot yang tujuannya
    memuat dirinya."""
    q = db.query(Slot)
    if status_filter is not None:
        q = q.filter(Slot.status == status_filter)

    if pengguna.peran in (PeranPengguna.PETUGAS, PeranPengguna.PETANI):
        q = q.filter(Slot.titik_kumpul_id == pengguna.titik_kumpul_id)
        return q.order_by(Slot.dibuat_pada.desc()).all()

    if pengguna.peran == PeranPengguna.PENERIMA:
        q = q.join(SlotTujuan, SlotTujuan.slot_id == Slot.id).filter(SlotTujuan.penerima_id == pengguna.penerima_id)
        return q.order_by(Slot.dibuat_pada.desc()).distinct().all()

    return []
