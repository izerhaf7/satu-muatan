"""Endpoint lot: muat (§9.5), bukti QR & serah terima (§9.7)."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_pengguna_aktif, wajib_peran
from app.database import get_db
from app.models import Komoditas, Lot, Partisipasi, Penerima, Pengguna, Pengiriman, Permintaan, SerahTerima, Slot
from app.models.enums import Atribusi, StatusPartisipasi, StatusPermintaan, StatusSlot
from app.schemas.lot import BuktiLotOut, LotOut, MuatPatchRequest, SerahTerimaCreate, SerahTerimaOut
from app.services import mesin
from app.services.konfigurasi import baca_konfigurasi
from app.services.otorisasi import pastikan_bisa_lihat_slot

router = APIRouter(tags=["lot"])


# ---------------------------------------------------------------------------
# Helper internal
# ---------------------------------------------------------------------------


def _ke_lot_out(lot: Lot, db: Session) -> LotOut:
    partisipasi = db.get(Partisipasi, lot.partisipasi_id)
    petani = db.get(Pengguna, partisipasi.petani_id) if partisipasi else None
    komoditas = db.get(Komoditas, partisipasi.komoditas_id) if partisipasi else None
    penerima = db.get(Penerima, lot.penerima_id) if lot.penerima_id else None
    return LotOut(
        id=lot.id,
        kode_qr=lot.kode_qr,
        partisipasi_id=lot.partisipasi_id,
        nama_petani=petani.nama if petani else "",
        nama_komoditas=komoditas.nama if komoditas else "",
        volume_kg=partisipasi.volume_kg if partisipasi else 0,
        penerima_id=lot.penerima_id,
        nama_penerima=penerima.nama if penerima else None,
        berat_aktual_kg=lot.berat_aktual_kg,
        foto_muat=lot.foto_muat,
        waktu_muat=lot.waktu_muat,
        catatan_muat=lot.catatan_muat,
        cacat_terlihat=lot.cacat_terlihat,
    )


def _bangun_penjelasan(atribusi: str, durasi_menit: int, ambang_menit: int) -> str:
    if atribusi == Atribusi.PETANI.value:
        return (
            f"Petani — cacat sudah terlihat sejak muat, sebelum barang berangkat. "
            f"Waktu tempuh {durasi_menit} menit (ambang rute ini {ambang_menit} menit)."
        )
    if atribusi == Atribusi.LOGISTIK.value:
        return (
            f"Logistik — tidak ada cacat di foto muat, tetapi waktu tempuh {durasi_menit} menit "
            f"melewati ambang {ambang_menit} menit untuk rute ini."
        )
    return (
        f"Tidak terbukti — tidak ada cacat di foto muat, dan waktu tempuh {durasi_menit} menit "
        f"masih di dalam ambang {ambang_menit} menit untuk rute ini."
    )


def _ke_serah_terima_out(st: SerahTerima) -> SerahTerimaOut:
    penjelasan = _bangun_penjelasan(st.atribusi.value, st.durasi_transit_menit, st.ambang_transit_menit)
    return SerahTerimaOut(
        id=st.id,
        lot_id=st.lot_id,
        penerima_id=st.penerima_id,
        waktu_bongkar=st.waktu_bongkar,
        keputusan=st.keputusan,
        persen_potongan=st.persen_potongan,
        alasan=st.alasan,
        durasi_transit_menit=st.durasi_transit_menit,
        ambang_transit_menit=st.ambang_transit_menit,
        atribusi=st.atribusi,
        penjelasan=penjelasan,
    )


def _ambang_slot(db: Session, slot: Slot) -> int:
    kecepatan = baca_konfigurasi(db, "kecepatan_rata_kmh")
    toleransi = baca_konfigurasi(db, "faktor_toleransi_transit")
    return mesin.ambang_transit_menit(float(slot.jarak_km), kecepatan, toleransi)


def _bukti_lot_out(lot: Lot, db: Session) -> BuktiLotOut:
    lot_out = _ke_lot_out(lot, db)
    partisipasi = db.get(Partisipasi, lot.partisipasi_id)
    slot = db.get(Slot, partisipasi.slot_id) if partisipasi else None
    pengiriman = db.query(Pengiriman).filter_by(slot_id=slot.id).one_or_none() if slot else None

    ambang = _ambang_slot(db, slot) if slot else 0
    durasi_berjalan: int | None = None
    if pengiriman is not None and pengiriman.waktu_berangkat is not None:
        acuan = pengiriman.waktu_tiba or datetime.now(timezone.utc)
        durasi_berjalan = int((acuan - pengiriman.waktu_berangkat).total_seconds() // 60)

    st = db.query(SerahTerima).filter_by(lot_id=lot.id).one_or_none()
    return BuktiLotOut(
        lot=lot_out,
        durasi_transit_berjalan_menit=durasi_berjalan,
        ambang_transit_menit=ambang,
        serah_terima=_ke_serah_terima_out(st) if st is not None else None,
    )


def _lot_atau_404(db: Session, lot_id: UUID) -> Lot:
    lot = db.get(Lot, lot_id)
    if lot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lot tidak ditemukan")
    return lot


# ---------------------------------------------------------------------------
# Endpoint — Muat (§9.5)
# ---------------------------------------------------------------------------


@router.get("/slot/{slot_id}/lot", response_model=list[LotOut])
def daftar_lot_slot(slot_id: UUID, pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    """Daftar lot sebuah slot — layar Muat (§9.5)."""
    slot = db.get(Slot, slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Slot tidak ditemukan")
    pastikan_bisa_lihat_slot(pengguna, slot)
    partisipasi_ids = [p.id for p in slot.partisipasi]
    if not partisipasi_ids:
        return []
    lots = db.query(Lot).filter(Lot.partisipasi_id.in_(partisipasi_ids)).all()
    return [_ke_lot_out(lot, db) for lot in lots]


@router.patch("/lot/{lot_id}/muat", response_model=LotOut)
def muat_lot(lot_id: UUID, body: MuatPatchRequest, pengguna=Depends(wajib_peran("KOPERASI")), db: Session = Depends(get_db)):
    """Timbang + foto + checkbox 'Ada cacat terlihat' (input kunci atribusi §6)."""
    lot = _lot_atau_404(db, lot_id)
    partisipasi = db.get(Partisipasi, lot.partisipasi_id)
    slot = db.get(Slot, partisipasi.slot_id) if partisipasi else None
    if slot is None or slot.koperasi_id != pengguna.koperasi_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Lot bukan milik koperasi Anda")
    if slot.status not in (StatusSlot.TERKUNCI, StatusSlot.DIMUAT):
        raise HTTPException(status.HTTP_409_CONFLICT, "Slot tidak dalam tahap pemuatan")

    lot.berat_aktual_kg = body.berat_aktual_kg
    lot.foto_muat = body.foto_muat_base64
    lot.cacat_terlihat = body.cacat_terlihat
    lot.catatan_muat = body.catatan_muat
    lot.waktu_muat = datetime.now(timezone.utc)

    if slot.status == StatusSlot.TERKUNCI:
        slot.status = StatusSlot.DIMUAT

    db.commit()
    db.refresh(lot)
    return _ke_lot_out(lot, db)


@router.post("/slot/{slot_id}/selesai-muat", response_model=list[LotOut])
def selesai_muat(slot_id: UUID, pengguna=Depends(wajib_peran("KOPERASI")), db: Session = Depends(get_db)):
    """Selesai muat -> slot JALAN, waktu berangkat tercatat (§9.5)."""
    slot = db.get(Slot, slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Slot tidak ditemukan")
    if slot.koperasi_id != pengguna.koperasi_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Slot bukan milik koperasi Anda")
    if slot.status not in (StatusSlot.TERKUNCI, StatusSlot.DIMUAT):
        raise HTTPException(status.HTTP_409_CONFLICT, "Slot tidak dalam tahap pemuatan")

    partisipasi_ids = [p.id for p in slot.partisipasi if p.status != StatusPartisipasi.BATAL]
    lots = db.query(Lot).filter(Lot.partisipasi_id.in_(partisipasi_ids)).all() if partisipasi_ids else []
    if not lots or any(lot.waktu_muat is None for lot in lots):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Semua lot wajib ditimbang sebelum selesai muat")

    sekarang = datetime.now(timezone.utc)
    slot.status = StatusSlot.JALAN
    for p in slot.partisipasi:
        if p.status in (StatusPartisipasi.TERKUNCI, StatusPartisipasi.DIMUAT):
            p.status = StatusPartisipasi.DIMUAT

    pengiriman = db.query(Pengiriman).filter_by(slot_id=slot.id).one_or_none()
    if pengiriman is not None:
        if pengiriman.waktu_berangkat is None:
            pengiriman.waktu_berangkat = sekarang
        pengiriman.status_vendor = "JALAN"

    db.commit()
    return [_ke_lot_out(lot, db) for lot in lots]


# ---------------------------------------------------------------------------
# Endpoint — Serah Terima (§9.7)
# ---------------------------------------------------------------------------


@router.get("/lot/masuk", response_model=list[BuktiLotOut])
def lot_masuk(pengguna=Depends(wajib_peran("PENERIMA")), db: Session = Depends(get_db)):
    """'Pilih dari daftar' (§9.7, K6): lot menuju penerima login yang belum
    diserahterimakan — jalur demo teraman."""
    lots = (
        db.query(Lot)
        .join(Partisipasi, Partisipasi.id == Lot.partisipasi_id)
        .join(Slot, Slot.id == Partisipasi.slot_id)
        .filter(Lot.penerima_id == pengguna.penerima_id)
        .filter(Slot.status.in_([StatusSlot.JALAN, StatusSlot.SELESAI]))
        .all()
    )
    hasil = []
    for lot in lots:
        if db.query(SerahTerima).filter_by(lot_id=lot.id).one_or_none() is not None:
            continue
        hasil.append(_bukti_lot_out(lot, db))
    return hasil


@router.get("/lot/qr/{kode_qr}", response_model=BuktiLotOut)
def bukti_lot(kode_qr: str, pengguna=Depends(wajib_peran("PENERIMA")), db: Session = Depends(get_db)):
    """Bukti lot dari scan QR: foto muat, berat, waktu, transit berjalan vs ambang."""
    lot = db.query(Lot).filter_by(kode_qr=kode_qr).one_or_none()
    if lot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lot tidak ditemukan")
    if lot.penerima_id != pengguna.penerima_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Lot ini bukan untuk Anda")
    return _bukti_lot_out(lot, db)


@router.post("/lot/{lot_id}/serah-terima", response_model=SerahTerimaOut, status_code=201)
def serah_terima(
    lot_id: UUID, body: SerahTerimaCreate, pengguna=Depends(wajib_peran("PENERIMA")), db: Session = Depends(get_db)
):
    """Terima / Terima dengan potongan / Tolak -> atribusi + PENJELASAN (§6, §9.7)."""
    lot = _lot_atau_404(db, lot_id)
    if lot.penerima_id != pengguna.penerima_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Lot ini bukan untuk Anda")
    if db.query(SerahTerima).filter_by(lot_id=lot.id).one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Lot ini sudah diserahterimakan")

    partisipasi = db.get(Partisipasi, lot.partisipasi_id)
    slot = db.get(Slot, partisipasi.slot_id) if partisipasi else None
    pengiriman = db.query(Pengiriman).filter_by(slot_id=slot.id).one_or_none() if slot else None
    if slot is None or pengiriman is None or pengiriman.waktu_berangkat is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Pengiriman belum berangkat")

    sekarang = datetime.now(timezone.utc)
    durasi_transit_menit = max(0, int((sekarang - pengiriman.waktu_berangkat).total_seconds() // 60))
    ambang_menit = _ambang_slot(db, slot)
    atribusi_str = mesin.tentukan_atribusi(lot.cacat_terlihat, durasi_transit_menit, ambang_menit)

    st = SerahTerima(
        lot_id=lot.id,
        penerima_id=pengguna.penerima_id,
        waktu_bongkar=sekarang,
        foto_bongkar=body.foto_bongkar_base64,
        keputusan=body.keputusan,
        persen_potongan=body.persen_potongan,
        alasan=body.alasan,
        durasi_transit_menit=durasi_transit_menit,
        ambang_transit_menit=ambang_menit,
        atribusi=Atribusi(atribusi_str),
    )
    db.add(st)

    # Perbarui pemenuhan permintaan yang terkait (K6) — basis volume komitmen (K3).
    if lot.penerima_id is not None and partisipasi is not None:
        kandidat = (
            db.query(Permintaan)
            .filter(
                Permintaan.slot_id == slot.id,
                Permintaan.penerima_id == lot.penerima_id,
                Permintaan.komoditas_id == partisipasi.komoditas_id,
                Permintaan.status.in_([StatusPermintaan.TERBUKA, StatusPermintaan.TERPENUHI_SEBAGIAN]),
            )
            .order_by(Permintaan.dibuat_pada)
            .all()
        )
        sisa = partisipasi.volume_kg
        for pm in kandidat:
            if sisa <= 0:
                break
            butuh = pm.volume_kg - pm.volume_terpenuhi_kg
            if butuh <= 0:
                continue
            tambahan = min(butuh, sisa)
            pm.volume_terpenuhi_kg += tambahan
            sisa -= tambahan
            pm.status = (
                StatusPermintaan.TERPENUHI if pm.volume_terpenuhi_kg >= pm.volume_kg else StatusPermintaan.TERPENUHI_SEBAGIAN
            )

    if partisipasi is not None:
        partisipasi.status = StatusPartisipasi.SELESAI

    # Slot selesai kalau semua lot-nya sudah diserahterimakan.
    partisipasi_ids = [p.id for p in slot.partisipasi if p.status != StatusPartisipasi.BATAL]
    semua_lot = db.query(Lot).filter(Lot.partisipasi_id.in_(partisipasi_ids)).all() if partisipasi_ids else []
    sudah_serah = {
        st_row.lot_id
        for st_row in db.query(SerahTerima).filter(SerahTerima.lot_id.in_([lot.id for lot in semua_lot])).all()
    }
    sudah_serah.add(lot.id)
    if semua_lot and all(lot.id in sudah_serah for lot in semua_lot):
        slot.status = StatusSlot.SELESAI

    db.commit()
    db.refresh(st)
    return _ke_serah_terima_out(st)
