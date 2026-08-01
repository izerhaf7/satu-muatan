"""Endpoint Berita Acara (§9.8) — FE merender halaman cetak window.print()."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_pengguna_aktif
from app.database import get_db
from app.models import Komoditas, Lot, Penerima, Pengguna, SerahTerima, Slot, TitikKumpul
from app.models.enums import StatusPartisipasi
from app.routers.lot import _ke_lot_out, _ke_serah_terima_out
from app.schemas.berita import BeritaAcaraOut, LotBeritaOut, OngkosPetaniOut
from app.schemas.master import TitikKumpulOut
from app.schemas.slot import RuteSegmenOut
from app.services.otorisasi import pastikan_bisa_lihat_slot

router = APIRouter(tags=["berita-acara"])


@router.get("/slot/{slot_id}/berita-acara", response_model=BeritaAcaraOut)
def berita_acara(slot_id: UUID, pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    """Agregat: lot + foto muat & bongkar, keputusan, atribusi, rincian ongkos
    per petani, selisih jaminan atap. Tanda tangan = garis kosong cetak (K4)."""
    slot = db.get(Slot, slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Slot tidak ditemukan")
    pastikan_bisa_lihat_slot(pengguna, slot)

    titik_kumpul = db.get(TitikKumpul, slot.titik_kumpul_id)

    tujuan = []
    for t in sorted(slot.tujuan, key=lambda x: x.urutan):
        penerima = db.get(Penerima, t.penerima_id)
        tujuan.append(
            RuteSegmenOut(
                urutan=t.urutan,
                penerima_id=t.penerima_id,
                nama_penerima=penerima.nama if penerima else "",
                jarak_segmen_km=float(t.jarak_segmen_km),
            )
        )

    partisipasi_aktif = [p for p in slot.partisipasi if p.status != StatusPartisipasi.BATAL]
    partisipasi_ids = [p.id for p in partisipasi_aktif]
    lots = db.query(Lot).filter(Lot.partisipasi_id.in_(partisipasi_ids)).all() if partisipasi_ids else []

    lot_baris = []
    for lot in lots:
        st = db.query(SerahTerima).filter_by(lot_id=lot.id).one_or_none()
        lot_baris.append(LotBeritaOut(lot=_ke_lot_out(lot, db), serah_terima=_ke_serah_terima_out(st, lot, db) if st else None))

    rincian_ongkos = []
    for p in partisipasi_aktif:
        if p.harga_final_per_kg is None:
            continue
        petani = db.get(Pengguna, p.petani_id)
        komoditas = db.get(Komoditas, p.komoditas_id)
        rincian_ongkos.append(
            OngkosPetaniOut(
                partisipasi_id=p.id,
                nama_petani=petani.nama if petani else "",
                nama_komoditas=komoditas.nama if komoditas else "",
                volume_kg=p.volume_kg,
                harga_atap_per_kg=p.harga_atap_per_kg,
                harga_final_per_kg=p.harga_final_per_kg,
                tagihan_rp=p.volume_kg * p.harga_final_per_kg,
                kembalian_rp=p.kembalian_rp,
            )
        )

    return BeritaAcaraOut(
        kode_slot=slot.kode,
        tanggal_kirim=slot.tanggal_kirim,
        titik_kumpul=TitikKumpulOut.model_validate(titik_kumpul),
        tujuan=tujuan,
        lot=lot_baris,
        rincian_ongkos=rincian_ongkos,
        biaya_total=slot.biaya_total,
        harga_final_per_kg=slot.harga_final_per_kg,
        selisih_jaminan_atap=slot.selisih_jaminan_atap,
        dibuat_pada=datetime.now(timezone.utc),
    )
