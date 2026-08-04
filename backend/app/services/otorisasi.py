"""Cek kepemilikan/visibilitas per peran (spec §12: tiga peran, cek sederhana).

K13 mengubah dasar otorisasi:
- PETUGAS (driver) tidak lagi "pemilik titik kumpul", tapi **petugas yang
  ditugaskan sistem** pada muatan itu (`Slot.petugas_id`).
- PETANI melihat muatan tempat dia benar-benar ikut serta, bukan semua muatan
  di titik kumpulnya — dia tidak pernah memilih muatan.
- PENERIMA mengakses lewat **nomor resi** (lihat `routers/lacak.py`); jalur
  berbasis `penerima_id` di sini hanya sisa kenyamanan untuk tujuan tetap.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Partisipasi, Slot, SlotTujuan
from app.models.enums import PeranPengguna, StatusPartisipasi, StatusSlot


def slot_terlihat_oleh(pengguna, slot: Slot) -> bool:
    if pengguna.peran == PeranPengguna.PETUGAS:
        # Driver yang ditugaskan; muatan tanpa petugas belum ditugaskan ke siapa pun.
        return slot.petugas_id == pengguna.id
    if pengguna.peran == PeranPengguna.PETANI:
        return any(
            p.petani_id == pengguna.id and p.status != StatusPartisipasi.BATAL for p in slot.partisipasi
        )
    if pengguna.peran == PeranPengguna.PENERIMA:
        return any(t.penerima_id == pengguna.penerima_id for t in slot.tujuan)
    return False


def pastikan_bisa_lihat_slot(pengguna, slot: Slot) -> None:
    if not slot_terlihat_oleh(pengguna, slot):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Slot tidak dapat diakses oleh peran ini")


def pastikan_petugas_muatan(pengguna, slot: Slot) -> None:
    """K13: hanya driver yang ditugaskan sistem yang boleh menutup, memuat,
    membatalkan, atau memajukan muatan ini."""
    if slot.petugas_id != pengguna.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Muatan ini bukan tugas Anda")


def query_slot_untuk_peran(db: Session, pengguna, status_filter: StatusSlot | None = None):
    """GET /api/slot — ter-scope per peran (K13):
    PETUGAS -> muatan yang ditugaskan padanya; PETANI -> muatan tempat dia ikut;
    PENERIMA -> muatan yang tujuannya memuat dirinya."""
    q = db.query(Slot)
    if status_filter is not None:
        q = q.filter(Slot.status == status_filter)

    if pengguna.peran == PeranPengguna.PETUGAS:
        q = q.filter(Slot.petugas_id == pengguna.id)
        return q.order_by(Slot.dibuat_pada.desc()).all()

    if pengguna.peran == PeranPengguna.PETANI:
        q = (
            q.join(Partisipasi, Partisipasi.slot_id == Slot.id)
            .filter(Partisipasi.petani_id == pengguna.id)
            .filter(Partisipasi.status != StatusPartisipasi.BATAL)
        )
        return q.order_by(Slot.dibuat_pada.desc()).distinct().all()

    if pengguna.peran == PeranPengguna.PENERIMA:
        q = q.join(SlotTujuan, SlotTujuan.slot_id == Slot.id).filter(SlotTujuan.penerima_id == pengguna.penerima_id)
        return q.order_by(Slot.dibuat_pada.desc()).distinct().all()

    return []
