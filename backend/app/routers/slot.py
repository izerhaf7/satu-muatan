"""Endpoint slot — jantung alur (§9.2–§9.4). GET /slot/{id} dipoll 3 detik."""

import math
from collections import Counter
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.base import Kontak, Titik
from app.auth import get_pengguna_aktif, wajib_peran
from app.database import get_db
from app.domain.armada import Tier
from app.models import (
    Kiriman,
    Komoditas,
    TitikKumpul,
    Lot,
    Partisipasi,
    Penerima,
    Pengguna,
    Pengiriman,
    Slot,
    TierKendaraan,
)
from app.models.enums import PeranPengguna, StatusPartisipasi, StatusSlot
from app.schemas.master import TitikKumpulOut
from app.schemas.slot import (
    GabungPratinjauRequest,
    GabungPratinjauResponse,
    GabungRequest,
    GabungResponse,
    LuapanKapasitasOut,
    PartisipasiOut,
    RencanaArmadaOut,
    ResiLotRingkasOut,
    RuteJemputOut,
    RuteSegmenOut,
    SensorNodeOut,
    SlotDetailOut,
    SlotItemOut,
    SensorNodeRequest,
    TierRingkasOut,
)
from app.services import mesin
from app.services.konfigurasi import baca_konfigurasi, baca_tiers_aktif
from app.services.pencocokan import STATUS_MUATAN_AKTIF, cutoff_lewat
from app.services.otorisasi import pastikan_bisa_lihat_slot, pastikan_petugas_muatan, query_slot_untuk_peran
from app.services.rute_snapshot import simpan_snapshot_rute
from app.services.vendor import dapatkan_adapter_vendor
from app.domain.armada import jarak_haversine_km

router = APIRouter(prefix="/slot", tags=["slot"])


@router.put("/{slot_id}/sensor-node", response_model=SensorNodeOut)
def tetapkan_sensor_node(
    slot_id: UUID,
    body: SensorNodeRequest,
    pengguna=Depends(wajib_peran("PETUGAS")),
    db: Session = Depends(get_db),
):
    """Kontrak penetapan node sensor oleh petugas pemegang muatan.

    Path tidak memuat URL atau credential Firebase. Backend membaca sensor server-side.
    """
    slot = db.get(Slot, slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Slot tidak ditemukan")
    pastikan_petugas_muatan(pengguna, slot)
    node_path = body.node_path.strip()
    if not node_path.startswith("/"):
        node_path = f"/{node_path}"
    if "?" in node_path or "#" in node_path:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Path node sensor tidak valid")
    slot.sensor_node_path = node_path
    db.commit()
    return SensorNodeOut(slot_id=slot.id, node_path=slot.sensor_node_path)


# ---------------------------------------------------------------------------
# Helper internal
# ---------------------------------------------------------------------------


def _tiers_dan_maks(db: Session) -> tuple[list[Tier], int]:
    return baca_tiers_aktif(db), baca_konfigurasi(db, "maks_kendaraan")


def _ringkas_tier(tiers: list[Tier]) -> str:
    hitung = Counter(t.kode for t in tiers)
    bagian = [f"{kode}x{n}" if n > 1 else kode for kode, n in sorted(hitung.items())]
    return "+".join(bagian)


def _dominan(tiers: list[Tier]) -> Tier:
    """Tier dominan untuk denormalisasi (K6) — kapasitas terbesar dalam rencana."""
    return max(tiers, key=lambda t: t.kapasitas_kg)


def _resi_slot(slot: Slot, db: Session, pengguna: Pengguna, tampilkan_resi: bool = True) -> list[ResiLotRingkasOut]:
    if not tampilkan_resi:
        return []

    query = db.query(Lot).join(Partisipasi, Lot.partisipasi_id == Partisipasi.id).filter(Partisipasi.slot_id == slot.id)
    if pengguna.peran == PeranPengguna.PETANI:
        query = query.filter(Partisipasi.petani_id == pengguna.id)
    elif pengguna.peran != PeranPengguna.PETUGAS or slot.petugas_id != pengguna.id:
        return []

    return [ResiLotRingkasOut(lot_id=lot.id, kode_qr=lot.kode_qr) for lot in query.order_by(Lot.kode_qr).all()]


def _ke_slot_item(
    slot: Slot,
    db: Session,
    pengguna: Pengguna,
    tampilkan_resi: bool = True,
    jarak_dari_driver_km: float | None = None,
) -> SlotItemOut:
    jumlah_petani = len({p.petani_id for p in slot.partisipasi if p.status != StatusPartisipasi.BATAL})
    kapasitas_rencana: int | None = None
    tier_ringkas: str | None = None

    if slot.status == StatusSlot.DIBUKA and slot.volume_terkunci_kg > 0:
        tiers, maks = _tiers_dan_maks(db)
        try:
            rencana = mesin.rencana_armada(slot.volume_terkunci_kg, float(slot.jarak_km), tiers, maks)
            kapasitas_rencana = rencana.kapasitas_total_kg
            tier_ringkas = _ringkas_tier(rencana.tier)
        except mesin.VolumeTerlaluBesar:
            pass
    elif slot.rencana_json:
        kapasitas_rencana = slot.rencana_json.get("kapasitas_total_kg")
        tier_ringkas = slot.rencana_json.get("tier_ringkas")

    return SlotItemOut(
        id=slot.id,
        kode=slot.kode,
        tanggal_kirim=slot.tanggal_kirim,
        cutoff_at=slot.cutoff_at,
        cutoff_lewat=cutoff_lewat(slot),
        status=slot.status,
        jarak_km=float(slot.jarak_km),
        jarak_dari_driver_km=jarak_dari_driver_km,
        volume_terkunci_kg=slot.volume_terkunci_kg,
        kapasitas_rencana_kg=kapasitas_rencana,
        tier_ringkas=tier_ringkas,
        jumlah_petani=jumlah_petani,
        resi=_resi_slot(slot, db, pengguna, tampilkan_resi),
    )


def _bangun_slot_detail(slot: Slot, db: Session, pengguna: Pengguna) -> SlotDetailOut:
    titik_kumpul = db.get(TitikKumpul, slot.titik_kumpul_id)
    tier_nama_by_kode = {t.kode: t.nama for t in db.query(TierKendaraan).all()}

    tujuan_out = []
    for t in sorted(slot.tujuan, key=lambda x: x.urutan):
        penerima = db.get(Penerima, t.penerima_id)
        tujuan_out.append(
            RuteSegmenOut(
                urutan=t.urutan,
                penerima_id=t.penerima_id,
                nama_penerima=penerima.nama if penerima else "",
                jarak_segmen_km=float(t.jarak_segmen_km),
                lat=penerima.lat if penerima else 0.0,
                lng=penerima.lng if penerima else 0.0,
            )
        )

    # K14: perhentian penjemputan — daftar alamat yang harus didatangi petugas.
    jemput_out = []
    for j in sorted(slot.jemput, key=lambda x: x.urutan):
        partisipasi_jemput = db.get(Partisipasi, j.partisipasi_id)
        petani_jemput = db.get(Pengguna, partisipasi_jemput.petani_id) if partisipasi_jemput else None
        jemput_out.append(
            RuteJemputOut(
                urutan=j.urutan,
                partisipasi_id=j.partisipasi_id,
                nama_petani=petani_jemput.nama if petani_jemput else "",
                alamat=j.alamat,
                jarak_segmen_km=float(j.jarak_segmen_km),
                lat=j.lat,
                lng=j.lng,
            )
        )

    partisipasi_out = []
    for p in slot.partisipasi:
        petani = db.get(Pengguna, p.petani_id)
        komoditas = db.get(Komoditas, p.komoditas_id)
        partisipasi_out.append(
            PartisipasiOut(
                id=p.id,
                petani_id=p.petani_id,
                nama_petani=petani.nama if petani else "",
                komoditas_id=p.komoditas_id,
                nama_komoditas=komoditas.nama if komoditas else "",
                volume_kg=p.volume_kg,
                harga_atap_per_kg=p.harga_atap_per_kg,
                harga_final_per_kg=p.harga_final_per_kg,
                kembalian_rp=p.kembalian_rp,
                status=p.status,
                bergabung_pada=p.bergabung_pada,
            )
        )

    volume_total = slot.volume_terkunci_kg
    harga_berjalan: int | None = None
    rencana_saat_ini: RencanaArmadaOut | None = None

    if slot.status == StatusSlot.DIBUKA:
        if volume_total > 0:
            tiers, maks = _tiers_dan_maks(db)
            try:
                rencana = mesin.rencana_armada(volume_total, float(slot.jarak_km), tiers, maks)
                harga_berjalan = math.ceil(rencana.biaya_total / volume_total)
                rencana_saat_ini = RencanaArmadaOut(
                    tier=[
                        TierRingkasOut(kode=t.kode, nama=tier_nama_by_kode.get(t.kode, t.kode), kapasitas_kg=t.kapasitas_kg)
                        for t in rencana.tier
                    ],
                    biaya_total=rencana.biaya_total,
                    kapasitas_total_kg=rencana.kapasitas_total_kg,
                )
            except mesin.VolumeTerlaluBesar:
                pass
    else:
        harga_berjalan = slot.harga_final_per_kg
        if slot.rencana_json:
            rencana_saat_ini = RencanaArmadaOut(
                tier=[
                    TierRingkasOut(
                        kode=t["kode"], nama=tier_nama_by_kode.get(t["kode"], t["kode"]), kapasitas_kg=t["kapasitas_kg"]
                    )
                    for t in slot.rencana_json.get("tier", [])
                ],
                biaya_total=slot.rencana_json.get("biaya_total", slot.biaya_total or 0),
                kapasitas_total_kg=slot.rencana_json.get("kapasitas_total_kg", 0),
            )

    # Dasarnya KEPESERTAAN, bukan peran — siapa pun yang punya panen di muatan
    # ini berhak melihat atapnya sendiri. (K14: hanya petani yang bisa jadi
    # peserta, tapi syaratnya tetap ditulis sebagai kepesertaan, bukan peran.)
    atap_saya: int | None = None
    hemat_saya: int | None = None
    punya = next(
        (p for p in slot.partisipasi if p.petani_id == pengguna.id and p.status != StatusPartisipasi.BATAL), None
    )
    if punya is not None:
        atap_saya = punya.harga_atap_per_kg
        acuan = harga_berjalan if harga_berjalan is not None else punya.harga_atap_per_kg
        hemat_saya = max(0, atap_saya - acuan)

    return SlotDetailOut(
        id=slot.id,
        kode=slot.kode,
        status=slot.status,
        tanggal_kirim=slot.tanggal_kirim,
        cutoff_at=slot.cutoff_at,
        cutoff_lewat=cutoff_lewat(slot),
        waktu_server=datetime.now(timezone.utc),
        jarak_km=float(slot.jarak_km),
        titik_kumpul=TitikKumpulOut.model_validate(titik_kumpul),
        jemput=jemput_out,
        tujuan=tujuan_out,
        volume_total_kg=volume_total,
        harga_berjalan_per_kg=harga_berjalan,
        rencana_saat_ini=rencana_saat_ini,
        partisipasi=partisipasi_out,
        atap_saya_per_kg=atap_saya,
        hemat_saya_per_kg=hemat_saya,
        biaya_total=slot.biaya_total,
        harga_final_per_kg=slot.harga_final_per_kg,
        selisih_jaminan_atap=slot.selisih_jaminan_atap,
        resi=_resi_slot(slot, db, pengguna),
    )


def _slot_atau_404(db: Session, slot_id: UUID) -> Slot:
    slot = db.get(Slot, slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Slot tidak ditemukan")
    return slot


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get("", response_model=list[SlotItemOut])
def daftar_slot(status: StatusSlot | None = None, pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    """Ter-scope per peran (K6): PETUGAS -> miliknya; PETANI -> slot titik kumpulnya;
    PENERIMA -> slot yang tujuannya memuat dirinya."""
    baris = query_slot_untuk_peran(db, pengguna, status)
    return [_ke_slot_item(s, db, pengguna) for s in baris]


# K13: `POST /slot` (buka slot) dan `POST /slot/pratinjau` DIHAPUS. Muatan bukan
# lagi sesuatu yang dibuka manusia — ia lahir sendiri dari kiriman petani
# (`services/pencocokan.py`). Petani hanya mengirim panen & memantau harga.


@router.get("/tersedia", response_model=list[SlotItemOut])
def slot_tersedia(pengguna=Depends(wajib_peran("PETUGAS")), db: Session = Depends(get_db)):
    """K14: PAPAN TUGAS — muatan yang belum punya driver dan berangkat dari titik
    kumpul petugas ini.

    K13 menugaskan driver otomatis saat muatan lahir, tanpa batas: satu petugas
    aktif menyerap SELURUH muatan di sistem, dan tidak ada satu pun endpoint yang
    bisa mengubahnya. Sekarang muatan menunggu diambil, dan pengambilan itu
    tindakan sadar driver."""
    if pengguna.terkini_lat is None or pengguna.terkini_lng is None:
        return []

    radius_km = float(baca_konfigurasi(db, "radius_papan_tugas_km"))
    kandidat = (
        db.query(Slot)
        .filter(Slot.petugas_id.is_(None), Slot.status == StatusSlot.DIBUKA)
        .order_by(Slot.tanggal_kirim, Slot.dibuat_pada)
        .all()
    )
    hasil = []
    for slot in kandidat:
        # Jarak diukur ke TITIK TERDEKAT dari wilayah kerja muatan — titik
        # kumpul, semua perhentian jemput, dan semua tujuan. Petugas menjemput
        # di lokasi petani, jadi muatan yang titik kumpulnya jauh tapi jemputnya
        # dekat tetap layak tampil (K14: rute dua tahap, jemput dulu).
        titik: list[tuple[float, float]] = []
        titik_kumpul = db.get(TitikKumpul, slot.titik_kumpul_id)
        if titik_kumpul is not None:
            titik.append((titik_kumpul.lat, titik_kumpul.lng))
        for j in sorted(slot.jemput, key=lambda x: x.urutan):
            titik.append((j.lat, j.lng))
        for t in sorted(slot.tujuan, key=lambda x: x.urutan):
            penerima = db.get(Penerima, t.penerima_id)
            if penerima is not None:
                titik.append((penerima.lat, penerima.lng))
        if not titik:
            continue
        jarak_min = min(
            jarak_haversine_km(pengguna.terkini_lat, pengguna.terkini_lng, lat, lng) for lat, lng in titik
        )
        if jarak_min <= radius_km:
            hasil.append(_ke_slot_item(slot, db, pengguna, tampilkan_resi=False, jarak_dari_driver_km=round(jarak_min, 2)))
    return hasil


@router.post("/{slot_id}/terima", response_model=SlotItemOut)
def terima_tugas(slot_id: UUID, pengguna=Depends(wajib_peran("PETUGAS")), db: Session = Depends(get_db)):
    """K14: petugas mengambil satu muatan — dan HANYA satu dalam satu waktu.

    Batasnya dari konfigurasi (`maks_muatan_aktif_per_petugas`), bukan angka di
    kode (CLAUDE.md aturan #1). Sopir tidak bisa membawa dua truk sekaligus;
    membiarkannya menumpuk tugas membuat papan tugas jadi hiasan."""
    slot = _slot_atau_404(db, slot_id)
    if slot.status != StatusSlot.DIBUKA:
        raise HTTPException(status.HTTP_409_CONFLICT, "Muatan ini sudah tidak terbuka untuk diambil")
    if slot.petugas_id is not None:
        if slot.petugas_id == pengguna.id:
            return _ke_slot_item(slot, db, pengguna)
        raise HTTPException(status.HTTP_409_CONFLICT, "Muatan ini sudah diambil petugas lain")

    maks_aktif = baca_konfigurasi(db, "maks_muatan_aktif_per_petugas")
    aktif = (
        db.query(Slot)
        .filter(Slot.petugas_id == pengguna.id, Slot.status.in_(STATUS_MUATAN_AKTIF))
        .count()
    )
    if aktif >= maks_aktif:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Kamu sedang membawa {aktif} muatan. Selesaikan dulu sebelum mengambil yang baru "
            f"(batas {maks_aktif} muatan aktif).",
        )

    slot.petugas_id = pengguna.id
    db.commit()
    db.refresh(slot)
    return _ke_slot_item(slot, db, pengguna)


@router.get("/{slot_id}", response_model=SlotDetailOut)
def detail_slot(slot_id: UUID, pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    """LAYAR UTAMA DEMO (§9.4). Dipoll 3 detik — harga berjalan, partisipasi,
    rencana armada, waktu_server."""
    slot = _slot_atau_404(db, slot_id)
    pastikan_bisa_lihat_slot(pengguna, slot)
    return _bangun_slot_detail(slot, db, pengguna)


@router.post(
    "/{slot_id}/gabung",
    response_model=GabungResponse,
    status_code=201,
    responses={409: {"model": LuapanKapasitasOut, "description": "LUAPAN_KAPASITAS (§5.5) — dialog dua pilihan"}},
)
def gabung_slot(slot_id: UUID, body: GabungRequest, pengguna=Depends(wajib_peran("PETANI")), db: Session = Depends(get_db)):
    """'Ikut kirim' — mengunci harga_atap_per_kg petani (tidak pernah berubah)."""
    slot = _slot_atau_404(db, slot_id)
    if slot.titik_kumpul_id != pengguna.titik_kumpul_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Slot bukan milik titik kumpul Anda")
    if slot.status != StatusSlot.DIBUKA:
        raise HTTPException(status.HTTP_409_CONFLICT, "Slot tidak lagi menerima peserta baru")
    komoditas = db.get(Komoditas, body.komoditas_id)
    if komoditas is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Komoditas tidak ditemukan")

    tiers, maks = _tiers_dan_maks(db)
    jarak_km = float(slot.jarak_km)
    try:
        atap = mesin.harga_atap_per_kg(body.volume_kg, jarak_km, tiers, maks)
    except (mesin.VolumeKosong, mesin.VolumeTerlaluBesar) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc))

    existing = [
        mesin.PartisipasiHarga(id=p.id, volume_kg=p.volume_kg, harga_atap_per_kg=p.harga_atap_per_kg)
        for p in slot.partisipasi
        if p.status != StatusPartisipasi.BATAL
    ]
    hasil_luapan = mesin.cek_luapan_kapasitas(body.volume_kg, existing, jarak_km, tiers, maks)

    if hasil_luapan.luapan:
        alternatif = (
            db.query(Slot)
            .filter(
                Slot.titik_kumpul_id == slot.titik_kumpul_id,
                Slot.tanggal_kirim == slot.tanggal_kirim,
                Slot.status == StatusSlot.DIBUKA,
                Slot.id != slot.id,
            )
            .first()
        )
        badan = LuapanKapasitasOut(
            kode="LUAPAN_KAPASITAS",
            harga_baru_per_kg=hasil_luapan.harga_baru_per_kg,
            jumlah_atap_terdampak=hasil_luapan.jumlah_atap_terdampak,
            slot_alternatif_id=alternatif.id if alternatif else None,
            pesan=(
                f"Bergabung dengan {body.volume_kg} kg akan menaikkan harga berjalan ke "
                f"Rp{hasil_luapan.harga_baru_per_kg}/kg, melampaui harga atap "
                f"{hasil_luapan.jumlah_atap_terdampak} peserta yang sudah bergabung. "
                "Silakan gabung ke slot berikutnya, atau minta petugas membuka slot kedua."
            ),
        )
        # Bentuk body 409 dibekukan sebagai LuapanKapasitasOut APA ADANYA di kontrak/openapi.yaml
        # (bukan dibungkus {"detail": ...} seperti HTTPException default) — pakai JSONResponse mentah.
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=badan.model_dump(mode="json"))

    partisipasi = Partisipasi(
        slot_id=slot.id,
        petani_id=pengguna.id,
        komoditas_id=body.komoditas_id,
        volume_kg=body.volume_kg,
        harga_atap_per_kg=atap,
        kembalian_rp=0,
        status=StatusPartisipasi.TERDAFTAR,
    )
    db.add(partisipasi)
    slot.volume_terkunci_kg += body.volume_kg
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Anda sudah bergabung dengan komoditas ini di slot ini")
    db.refresh(partisipasi)

    petani_nama = pengguna.nama
    return GabungResponse(
        partisipasi=PartisipasiOut(
            id=partisipasi.id,
            petani_id=partisipasi.petani_id,
            nama_petani=petani_nama,
            komoditas_id=partisipasi.komoditas_id,
            nama_komoditas=komoditas.nama,
            volume_kg=partisipasi.volume_kg,
            harga_atap_per_kg=partisipasi.harga_atap_per_kg,
            harga_final_per_kg=partisipasi.harga_final_per_kg,
            kembalian_rp=partisipasi.kembalian_rp,
            status=partisipasi.status,
            bergabung_pada=partisipasi.bergabung_pada,
        ),
        harga_atap_per_kg=atap,
    )


@router.post("/{slot_id}/gabung/pratinjau", response_model=GabungPratinjauResponse)
def pratinjau_gabung(
    slot_id: UUID, body: GabungPratinjauRequest, pengguna=Depends(wajib_peran("PETANI")), db: Session = Depends(get_db)
):
    """Peringatan dini sebelum submit: atap, harga berjalan baru, potensi luapan."""
    slot = _slot_atau_404(db, slot_id)
    if slot.titik_kumpul_id != pengguna.titik_kumpul_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Slot bukan milik titik kumpul Anda")

    tiers, maks = _tiers_dan_maks(db)
    jarak_km = float(slot.jarak_km)
    try:
        atap = mesin.harga_atap_per_kg(body.volume_kg, jarak_km, tiers, maks)
    except (mesin.VolumeKosong, mesin.VolumeTerlaluBesar) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc))

    existing = [
        mesin.PartisipasiHarga(id=p.id, volume_kg=p.volume_kg, harga_atap_per_kg=p.harga_atap_per_kg)
        for p in slot.partisipasi
        if p.status != StatusPartisipasi.BATAL
    ]
    hasil_luapan = mesin.cek_luapan_kapasitas(body.volume_kg, existing, jarak_km, tiers, maks)

    pesan = None
    if hasil_luapan.luapan:
        pesan = (
            f"Bergabung akan menaikkan harga berjalan ke Rp{hasil_luapan.harga_baru_per_kg}/kg, "
            f"melampaui atap {hasil_luapan.jumlah_atap_terdampak} peserta yang sudah bergabung."
        )

    return GabungPratinjauResponse(
        harga_atap_per_kg=atap,
        harga_berjalan_baru_per_kg=hasil_luapan.harga_baru_per_kg,
        luapan=hasil_luapan.luapan,
        pesan=pesan,
    )


@router.post("/{slot_id}/tutup", response_model=SlotDetailOut)
def tutup_slot(slot_id: UUID, pengguna=Depends(wajib_peran("PETUGAS")), db: Session = Depends(get_db)):
    """Cutoff (§5.4): tetapkan harga final + jaminan atap, kunci rencana armada,
    buat lot per partisipasi (alokasi penerima — K6), pesan ke vendor."""
    slot = _slot_atau_404(db, slot_id)
    pastikan_petugas_muatan(pengguna, slot)
    if slot.status != StatusSlot.DIBUKA:
        raise HTTPException(status.HTTP_409_CONFLICT, "Slot sudah ditutup atau dibatalkan")

    partisipasi_aktif = [p for p in slot.partisipasi if p.status == StatusPartisipasi.TERDAFTAR]
    if not partisipasi_aktif:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Belum ada peserta yang bergabung")

    tiers, maks = _tiers_dan_maks(db)
    jarak_km = float(slot.jarak_km)
    partisipasi_harga = [
        mesin.PartisipasiHarga(id=p.id, volume_kg=p.volume_kg, harga_atap_per_kg=p.harga_atap_per_kg)
        for p in partisipasi_aktif
    ]
    hasil = mesin.tetapkan_harga_final(partisipasi_harga, jarak_km, tiers, maks)

    for p in partisipasi_aktif:
        h_i = min(hasil.harga_final_per_kg, p.harga_atap_per_kg)
        p.harga_final_per_kg = h_i
        p.kembalian_rp = hasil.kembalian[p.id]
        p.status = StatusPartisipasi.TERKUNCI

    tier_dominan = _dominan(hasil.rencana.tier)
    tier_dominan_row = db.query(TierKendaraan).filter_by(kode=tier_dominan.kode).one()

    slot.status = StatusSlot.TERKUNCI
    slot.biaya_total = hasil.biaya_total
    slot.harga_final_per_kg = hasil.harga_final_per_kg
    slot.selisih_jaminan_atap = hasil.subsidi_koperasi
    slot.tier_terpilih_id = tier_dominan_row.id
    slot.jumlah_kendaraan = len(hasil.rencana.tier)
    slot.rencana_json = {
        "tier": [{"kode": t.kode, "kapasitas_kg": t.kapasitas_kg} for t in hasil.rencana.tier],
        "biaya_total": hasil.rencana.biaya_total,
        "kapasitas_total_kg": hasil.rencana.kapasitas_total_kg,
        "tier_ringkas": _ringkas_tier(hasil.rencana.tier),
    }

    # K13: alokasi lot -> tujuan = tujuan yang DIMINTA petani itu sendiri di
    # kirimannya. Tidak ada lagi pencocokan permintaan: barang tiap petani pergi
    # ke alamat yang dia tulis, bukan ke alamat pemesan orang lain.
    tujuan_pertama_id = min(slot.tujuan, key=lambda t: t.urutan).penerima_id if slot.tujuan else None
    penerima_by_partisipasi = {
        k.partisipasi_id: k.penerima_id
        for k in db.query(Kiriman).filter(Kiriman.slot_id == slot.id).all()
        if k.partisipasi_id is not None and k.penerima_id is not None
    }

    partisipasi_terurut = sorted(partisipasi_aktif, key=lambda p: p.bergabung_pada)
    for idx, p in enumerate(partisipasi_terurut, start=1):
        lot = Lot(
            partisipasi_id=p.id,
            # Kode ini yang dipakai penerima sebagai NOMOR RESI (K13).
            kode_qr=f"LOT-{slot.kode}-{idx:02d}",
            penerima_id=penerima_by_partisipasi.get(p.id, tujuan_pertama_id),
            grade_asal=5,  # default optimis — grade riil dinilai petugas saat muat (§6.1)
        )
        db.add(lot)

    # Pesan ke vendor (MockVendorAdapter, K5).
    titik_kumpul = db.get(TitikKumpul, slot.titik_kumpul_id)
    if titik_kumpul is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Titik kumpul tidak ditemukan")
    titik = [Titik(lat=titik_kumpul.lat, lng=titik_kumpul.lng, label="Titik kumpul")]
    for t in sorted(slot.tujuan, key=lambda x: x.urutan):
        penerima = db.get(Penerima, t.penerima_id)
        if penerima is not None:
            titik.append(Titik(lat=penerima.lat, lng=penerima.lng, label=penerima.nama))

    adapter = dapatkan_adapter_vendor(db)
    kuotasi = adapter.kuotasi(titik, tier_dominan.kode)
    pesanan = adapter.pesan(kuotasi.kuotasi_id, Kontak(nama=pengguna.nama, no_hp=pengguna.no_hp))
    pengiriman = Pengiriman(
        slot_id=slot.id,
        vendor=adapter.nama,
        vendor_ref=pesanan.vendor_ref,
        status_vendor=pesanan.status,
        kuotasi_json=kuotasi.rincian,
    )
    db.add(pengiriman)
    db.flush()
    # Canonical price, lots, vendor order, and Pengiriman commit BEFORE optional
    # provider snapshot. Snapshot owns a later best-effort transaction.
    db.commit()
    db.refresh(pengiriman)
    db.refresh(slot)
    simpan_snapshot_rute(db, pengiriman, slot)
    db.refresh(slot)
    return _bangun_slot_detail(slot, db, pengguna)


@router.post("/{slot_id}/batal", response_model=SlotDetailOut)
def batal_slot(slot_id: UUID, pengguna=Depends(wajib_peran("PETUGAS")), db: Session = Depends(get_db)):
    slot = _slot_atau_404(db, slot_id)
    pastikan_petugas_muatan(pengguna, slot)
    if slot.status in (StatusSlot.SELESAI, StatusSlot.BATAL):
        raise HTTPException(status.HTTP_409_CONFLICT, "Slot sudah selesai atau sudah dibatalkan")

    slot.status = StatusSlot.BATAL
    for p in slot.partisipasi:
        if p.status != StatusPartisipasi.BATAL:
            p.status = StatusPartisipasi.BATAL

    db.commit()
    db.refresh(slot)
    return _bangun_slot_detail(slot, db, pengguna)
