"""Riwayat partisipasi petani (layar Riwayat, §2.5)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import wajib_peran
from app.database import get_db
from app.models import Komoditas, Lot, Partisipasi, Slot
from app.schemas.riwayat import PartisipasiRiwayatOut
from app.schemas.slot import ResiLotRingkasOut

router = APIRouter(tags=["riwayat"])


@router.get("/partisipasi/saya", response_model=list[PartisipasiRiwayatOut])
def partisipasi_saya(pengguna=Depends(wajib_peran("PETANI")), db: Session = Depends(get_db)):
    """Riwayat ikut kirim + kembalian milik petani login."""
    baris = db.query(Partisipasi).filter_by(petani_id=pengguna.id).order_by(Partisipasi.bergabung_pada.desc()).all()
    hasil = []
    for p in baris:
        slot = db.get(Slot, p.slot_id)
        if slot is None:
            continue
        komoditas = db.get(Komoditas, p.komoditas_id)
        hasil.append(
            PartisipasiRiwayatOut(
                id=p.id,
                slot_id=p.slot_id,
                slot_kode=slot.kode,
                tanggal_kirim=slot.tanggal_kirim,
                nama_komoditas=komoditas.nama if komoditas else "",
                volume_kg=p.volume_kg,
                harga_atap_per_kg=p.harga_atap_per_kg,
                harga_final_per_kg=p.harga_final_per_kg,
                kembalian_rp=p.kembalian_rp,
                status=p.status,
                resi=[
                    ResiLotRingkasOut(lot_id=lot.id, kode_qr=lot.kode_qr)
                    for lot in db.query(Lot).filter(Lot.partisipasi_id == p.id).order_by(Lot.kode_qr).all()
                ],
            )
        )
    return hasil
