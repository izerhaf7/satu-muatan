"""Endpoint pelacakan (§9.6)."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_pengguna_aktif, wajib_peran
from app.database import get_db
from app.models import JejakPosisi, Lot, Partisipasi, Penerima, Pengiriman, Slot
from app.models.enums import SumberPosisi
from app.schemas.lacak import PengirimanOut, PosisiOut, TimelineOut
from app.services import mesin
from app.services.konfigurasi import baca_konfigurasi
from app.services.otorisasi import pastikan_bisa_lihat_slot

router = APIRouter(tags=["lacak"])

# K5: state machine simulasi MockVendor — urutan tetap, dimajukan eksplisit lewat /majukan.
_URUTAN_STATUS = ["DIPESAN", "MENUJU_MUAT", "JALAN", "TIBA"]


def _ambang_slot(db: Session, slot: Slot) -> int:
    kecepatan = baca_konfigurasi(db, "kecepatan_rata_kmh")
    toleransi = baca_konfigurasi(db, "faktor_toleransi_transit")
    return mesin.ambang_transit_menit(float(slot.jarak_km), kecepatan, toleransi)


def _ke_pengiriman_out(pengiriman: Pengiriman, slot: Slot, db: Session) -> PengirimanOut:
    partisipasi_ids = [p.id for p in slot.partisipasi]
    lots = db.query(Lot).filter(Lot.partisipasi_id.in_(partisipasi_ids)).all() if partisipasi_ids else []
    waktu_muat = [lot.waktu_muat for lot in lots if lot.waktu_muat is not None]
    dimuat = max(waktu_muat) if waktu_muat else None

    ambang = _ambang_slot(db, slot)
    estimasi_tiba = (
        pengiriman.waktu_berangkat + timedelta(minutes=ambang) if pengiriman.waktu_berangkat is not None else None
    )

    jejak = (
        db.query(JejakPosisi)
        .filter_by(pengiriman_id=pengiriman.id)
        .order_by(JejakPosisi.waktu)
        .all()
    )

    return PengirimanOut(
        id=pengiriman.id,
        slot_id=pengiriman.slot_id,
        vendor=pengiriman.vendor,
        vendor_ref=pengiriman.vendor_ref,
        status_vendor=pengiriman.status_vendor,
        timeline=TimelineOut(
            dipesan=pengiriman.dibuat_pada,
            dimuat=dimuat,
            berangkat=pengiriman.waktu_berangkat,
            tiba=pengiriman.waktu_tiba,
        ),
        estimasi_tiba=estimasi_tiba,
        ambang_transit_menit=ambang,
        jejak=[PosisiOut(lat=j.lat, lng=j.lng, waktu=j.waktu, sumber=j.sumber) for j in jejak],
    )


@router.get("/slot/{slot_id}/pengiriman", response_model=PengirimanOut)
def pengiriman_slot(slot_id: UUID, pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    """Timeline + estimasi tiba (dari ambang transit) + jejak posisi."""
    slot = db.get(Slot, slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Slot tidak ditemukan")
    pastikan_bisa_lihat_slot(pengguna, slot)
    pengiriman = db.query(Pengiriman).filter_by(slot_id=slot.id).one_or_none()
    if pengiriman is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Slot ini belum punya pengiriman (belum ditutup)")
    return _ke_pengiriman_out(pengiriman, slot, db)


@router.post("/pengiriman/{pengiriman_id}/majukan", response_model=PengirimanOut)
def majukan_pengiriman(pengiriman_id: UUID, pengguna=Depends(wajib_peran("KOPERASI")), db: Session = Depends(get_db)):
    """Majukan state simulasi MockVendor satu langkah (K5) — deterministik, untuk demo."""
    pengiriman = db.get(Pengiriman, pengiriman_id)
    if pengiriman is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pengiriman tidak ditemukan")
    slot = db.get(Slot, pengiriman.slot_id)
    if slot is None or slot.koperasi_id != pengguna.koperasi_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Pengiriman bukan milik koperasi Anda")

    saat_ini = pengiriman.status_vendor or "DIPESAN"
    idx = _URUTAN_STATUS.index(saat_ini) if saat_ini in _URUTAN_STATUS else 0
    if idx < len(_URUTAN_STATUS) - 1:
        idx += 1
        pengiriman.status_vendor = _URUTAN_STATUS[idx]
        sekarang = datetime.now(timezone.utc)

        if _URUTAN_STATUS[idx] == "JALAN" and pengiriman.waktu_berangkat is None:
            pengiriman.waktu_berangkat = sekarang

        if _URUTAN_STATUS[idx] == "TIBA":
            if pengiriman.waktu_tiba is None:
                pengiriman.waktu_tiba = sekarang
            tujuan_terakhir = max(slot.tujuan, key=lambda t: t.urutan) if slot.tujuan else None
            penerima = db.get(Penerima, tujuan_terakhir.penerima_id) if tujuan_terakhir else None
            db.add(
                JejakPosisi(
                    pengiriman_id=pengiriman.id,
                    lat=penerima.lat if penerima else None,
                    lng=penerima.lng if penerima else None,
                    waktu=sekarang,
                    sumber=SumberPosisi.SIMULASI,
                )
            )
        db.commit()
        db.refresh(pengiriman)

    return _ke_pengiriman_out(pengiriman, slot, db)
