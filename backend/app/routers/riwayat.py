"""Riwayat partisipasi petani (layar Riwayat, §2.5)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import wajib_peran
from app.database import get_db
from app.models import Komoditas, Partisipasi, Slot
from app.schemas.riwayat import PartisipasiRiwayatOut

router = APIRouter(tags=["riwayat"])


@router.get("/partisipasi/saya", response_model=list[PartisipasiRiwayatOut])
def partisipasi_saya(pengguna=Depends(wajib_peran("PETANI")), db: Session = Depends(get_db)):
    """Riwayat ikut kirim + kembalian milik petani login."""
    baris = db.query(Partisipasi).filter_by(petani_id=pengguna.id).order_by(Partisipasi.bergabung_pada.desc()).all()
    hasil = []
    for p in baris:
        slot = db.get(Slot, p.slot_id)
        komoditas = db.get(Komoditas, p.komoditas_id)
        hasil.append(
            PartisipasiRiwayatOut(
                id=p.id,
                slot_id=p.slot_id,
                slot_kode=slot.kode if slot else "",
                tanggal_kirim=slot.tanggal_kirim if slot else None,
                nama_komoditas=komoditas.nama if komoditas else "",
                volume_kg=p.volume_kg,
                harga_atap_per_kg=p.harga_atap_per_kg,
                harga_final_per_kg=p.harga_final_per_kg,
                kembalian_rp=p.kembalian_rp,
                status=p.status,
            )
        )
    return hasil
