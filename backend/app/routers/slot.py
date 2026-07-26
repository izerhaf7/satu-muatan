"""Endpoint slot — jantung alur (§9.2–§9.4). GET /slot/{id} dipoll 3 detik."""

import math
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.adapters.base import Kontak, Titik
from app.auth import get_pengguna_aktif, wajib_peran
from app.database import get_db
from app.domain.armada import Tier, TujuanInput
from app.models import (
    Komoditas,
    Koperasi,
    Lot,
    Partisipasi,
    Penerima,
    Pengguna,
    Pengiriman,
    Permintaan,
    Slot,
    SlotTujuan,
    TierKendaraan,
)
from app.models.enums import PeranPengguna, StatusPartisipasi, StatusPermintaan, StatusSlot
from app.schemas.master import KoperasiOut
from app.schemas.slot import (
    GabungPratinjauRequest,
    GabungPratinjauResponse,
    GabungRequest,
    GabungResponse,
    LuapanKapasitasOut,
    PartisipasiOut,
    PratinjauSlotRequest,
    PratinjauSlotResponse,
    RencanaArmadaOut,
    RuteSegmenOut,
    SkenarioHargaOut,
    SlotCreate,
    SlotDetailOut,
    SlotItemOut,
    TierRingkasOut,
)
from app.services import mesin
from app.services.konfigurasi import baca_konfigurasi, baca_tiers_aktif
from app.services.otorisasi import pastikan_bisa_lihat_slot, query_slot_untuk_peran
from app.services.vendor import dapatkan_adapter_vendor

router = APIRouter(prefix="/slot", tags=["slot"])


# ---------------------------------------------------------------------------
# Helper internal
# ---------------------------------------------------------------------------


def _tiers_dan_maks(db: Session) -> tuple[list[Tier], int]:
    return baca_tiers_aktif(db), baca_konfigurasi(db, "maks_kendaraan")


def _ringkas_tier(tiers: list[Tier]) -> str:
    hitung = Counter(t.kode for t in tiers)
    bagian = [f"{kode}x{n}" if n > 1 else kode for kode, n in sorted(hitung.items())]
    return "+".join(bagian)


def _koperasi_pengguna(db: Session, pengguna: Pengguna) -> Koperasi:
    if pengguna.koperasi_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pengguna ini tidak terhubung ke koperasi")
    koperasi = db.get(Koperasi, pengguna.koperasi_id)
    if koperasi is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Koperasi tidak ditemukan")
    return koperasi


def _hitung_nn_slot(db: Session, koperasi_id: UUID, tanggal_kirim) -> int:
    jumlah = db.query(Slot).filter_by(koperasi_id=koperasi_id, tanggal_kirim=tanggal_kirim).count()
    return jumlah + 1


def _muat_penerima(db: Session, ids: list[UUID]) -> dict[UUID, Penerima]:
    baris = db.query(Penerima).filter(Penerima.id.in_(ids)).all()
    ditemukan = {p.id: p for p in baris}
    hilang = [str(i) for i in ids if i not in ditemukan]
    if hilang:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Penerima tidak ditemukan: {', '.join(hilang)}")
    return ditemukan


def _bangun_rute(db: Session, koperasi: Koperasi, tujuan_ids: list[UUID]):
    penerima_by_id = _muat_penerima(db, tujuan_ids)
    faktor_jalan = baca_konfigurasi(db, "faktor_jalan")
    tujuan_input = [
        TujuanInput(penerima_id=pid, lat=penerima_by_id[pid].lat, lng=penerima_by_id[pid].lng) for pid in tujuan_ids
    ]
    urutan = mesin.urutkan_tujuan_nearest_neighbor((koperasi.lat, koperasi.lng), tujuan_input, faktor_jalan)
    jarak_total = sum(t.jarak_segmen_km for t in urutan)
    return urutan, jarak_total, penerima_by_id


def _dominan(tiers: list[Tier]) -> Tier:
    """Tier dominan untuk denormalisasi (K6) — kapasitas terbesar dalam rencana."""
    return max(tiers, key=lambda t: t.kapasitas_kg)


def _ke_slot_item(slot: Slot, db: Session) -> SlotItemOut:
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
        status=slot.status,
        jarak_km=float(slot.jarak_km),
        volume_terkunci_kg=slot.volume_terkunci_kg,
        kapasitas_rencana_kg=kapasitas_rencana,
        tier_ringkas=tier_ringkas,
        jumlah_petani=jumlah_petani,
    )


def _bangun_slot_detail(slot: Slot, db: Session, pengguna: Pengguna) -> SlotDetailOut:
    koperasi = db.get(Koperasi, slot.koperasi_id)
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

    atap_saya: int | None = None
    hemat_saya: int | None = None
    if pengguna.peran == PeranPengguna.PETANI:
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
        waktu_server=datetime.now(timezone.utc),
        jarak_km=float(slot.jarak_km),
        koperasi=KoperasiOut.model_validate(koperasi),
        tujuan=tujuan_out,
        volume_total_kg=volume_total,
        harga_berjalan_per_kg=harga_berjalan,
        rencana_saat_ini=rencana_saat_ini,
        partisipasi=partisipasi_out,
        atap_saya_per_kg=atap_saya,
        hemat_saya_per_kg=hemat_saya,
        biaya_total=slot.biaya_total,
        harga_final_per_kg=slot.harga_final_per_kg,
        subsidi_koperasi=slot.subsidi_koperasi,
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
    """Ter-scope per peran (K6): KOPERASI -> miliknya; PETANI -> slot koperasinya;
    PENERIMA -> slot yang tujuannya memuat dirinya."""
    baris = query_slot_untuk_peran(db, pengguna, status)
    return [_ke_slot_item(s, db) for s in baris]


@router.post("", response_model=SlotDetailOut, status_code=201)
def buka_slot(body: SlotCreate, pengguna=Depends(wajib_peran("KOPERASI")), db: Session = Depends(get_db)):
    """Buka slot baru (§9.3). Server menghitung urutan drop nearest-neighbor + jarak_km."""
    koperasi = _koperasi_pengguna(db, pengguna)
    if koperasi.kode is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Koperasi belum punya kode singkat (kolom `kode`)")

    urutan, jarak_total, _penerima = _bangun_rute(db, koperasi, body.tujuan)

    nn = _hitung_nn_slot(db, koperasi.id, body.tanggal_kirim)
    kode_slot = f"SM-{body.tanggal_kirim:%Y%m%d}-{koperasi.kode}-{nn:02d}"

    slot = Slot(
        kode=kode_slot,
        koperasi_id=koperasi.id,
        tanggal_kirim=body.tanggal_kirim,
        cutoff_at=body.cutoff_at,
        status=StatusSlot.DIBUKA,
        jarak_km=Decimal(str(round(jarak_total, 2))),
        volume_terkunci_kg=0,
        subsidi_koperasi=0,
    )
    db.add(slot)
    db.flush()

    for t in urutan:
        db.add(
            SlotTujuan(
                slot_id=slot.id,
                penerima_id=t.penerima_id,
                urutan=t.urutan,
                jarak_segmen_km=Decimal(str(round(t.jarak_segmen_km, 2))),
            )
        )

    if body.permintaan_ids:
        permintaan_baris = db.query(Permintaan).filter(Permintaan.id.in_(body.permintaan_ids)).all()
        ditemukan_ids = {p.id for p in permintaan_baris}
        hilang = [str(i) for i in body.permintaan_ids if i not in ditemukan_ids]
        if hilang:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Permintaan tidak ditemukan: {', '.join(hilang)}")
        for p in permintaan_baris:
            p.slot_id = slot.id

    db.commit()
    db.refresh(slot)
    return _bangun_slot_detail(slot, db, pengguna)


@router.post("/pratinjau", response_model=PratinjauSlotResponse)
def pratinjau_slot(body: PratinjauSlotRequest, pengguna=Depends(wajib_peran("KOPERASI")), db: Session = Depends(get_db)):
    """Pratinjau §9.3: jarak rute + tabel harga/kg pada berbagai skenario volume."""
    koperasi = _koperasi_pengguna(db, pengguna)
    urutan, jarak_total, penerima_by_id = _bangun_rute(db, koperasi, body.tujuan)

    rute = [
        RuteSegmenOut(
            urutan=t.urutan,
            penerima_id=t.penerima_id,
            nama_penerima=penerima_by_id[t.penerima_id].nama,
            jarak_segmen_km=round(t.jarak_segmen_km, 2),
        )
        for t in urutan
    ]

    tiers, maks = _tiers_dan_maks(db)
    tabel_harga = []
    for volume in body.skenario_volume:
        try:
            rencana = mesin.rencana_armada(volume, jarak_total, tiers, maks)
        except (mesin.VolumeKosong, mesin.VolumeTerlaluBesar) as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"volume {volume} kg: {exc}")
        tabel_harga.append(
            SkenarioHargaOut(
                volume_kg=volume,
                harga_per_kg=math.ceil(rencana.biaya_total / volume),
                biaya_total=rencana.biaya_total,
                kendaraan=[t.kode for t in rencana.tier],
            )
        )

    return PratinjauSlotResponse(jarak_km=round(jarak_total, 2), rute=rute, tabel_harga=tabel_harga)


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
    if slot.koperasi_id != pengguna.koperasi_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Slot bukan milik koperasi Anda")
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
                Slot.koperasi_id == slot.koperasi_id,
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
                "Silakan gabung ke slot berikutnya, atau minta koperasi membuka slot kedua."
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
    if slot.koperasi_id != pengguna.koperasi_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Slot bukan milik koperasi Anda")

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
def tutup_slot(slot_id: UUID, pengguna=Depends(wajib_peran("KOPERASI")), db: Session = Depends(get_db)):
    """Cutoff (§5.4): tetapkan harga final + jaminan atap, kunci rencana armada,
    buat lot per partisipasi (alokasi penerima — K6), pesan ke vendor."""
    slot = _slot_atau_404(db, slot_id)
    if slot.koperasi_id != pengguna.koperasi_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Slot bukan milik koperasi Anda")
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
    slot.subsidi_koperasi = hasil.subsidi_koperasi
    slot.tier_terpilih_id = tier_dominan_row.id
    slot.jumlah_kendaraan = len(hasil.rencana.tier)
    slot.rencana_json = {
        "tier": [{"kode": t.kode, "kapasitas_kg": t.kapasitas_kg} for t in hasil.rencana.tier],
        "biaya_total": hasil.rencana.biaya_total,
        "kapasitas_total_kg": hasil.rencana.kapasitas_total_kg,
        "tier_ringkas": _ringkas_tier(hasil.rencana.tier),
    }

    # Alokasi lot -> penerima: cocokkan permintaan (nearest) atau tujuan pertama (K6).
    urutan_by_penerima = {t.penerima_id: t.urutan for t in slot.tujuan}
    permintaan_slot = db.query(Permintaan).filter_by(slot_id=slot.id).all()
    tujuan_pertama_id = min(slot.tujuan, key=lambda t: t.urutan).penerima_id if slot.tujuan else None

    partisipasi_terurut = sorted(partisipasi_aktif, key=lambda p: p.bergabung_pada)
    # K11: kuota permintaan dilacak DALAM loop ini juga — volume_terpenuhi_kg baru
    # bertambah saat serah terima, jadi tanpa pelacakan lokal semua lot komoditas
    # sama bisa membanjiri permintaan pertama walau kuotanya sudah habis dialokasi.
    teralokasi_kg: dict = {pm.id: 0 for pm in permintaan_slot}
    for idx, p in enumerate(partisipasi_terurut, start=1):
        sekomoditas = [pm for pm in permintaan_slot if pm.komoditas_id == p.komoditas_id]
        kandidat = [
            pm for pm in sekomoditas if pm.volume_terpenuhi_kg + teralokasi_kg[pm.id] < pm.volume_kg
        ]
        if not kandidat:
            # Semua kuota sekomoditas habis → luber ke pemohon komoditas yang sama
            # (pemenuhan-lebih), bukan ke drop pertama — demo §11.2 (4 lot kubis,
            # 1 permintaan 300 kg) bergantung pada perilaku ini.
            kandidat = sekomoditas
        if kandidat:
            kandidat.sort(key=lambda pm: urutan_by_penerima.get(pm.penerima_id, 10**6))
            penerima_id = kandidat[0].penerima_id
            teralokasi_kg[kandidat[0].id] += p.volume_kg
        else:
            penerima_id = tujuan_pertama_id

        lot = Lot(
            partisipasi_id=p.id,
            kode_qr=f"LOT-{slot.kode}-{idx:02d}",
            penerima_id=penerima_id,
            cacat_terlihat=False,
        )
        db.add(lot)

    # Pesan ke vendor (MockVendorAdapter, K5).
    koperasi = db.get(Koperasi, slot.koperasi_id)
    titik = [Titik(lat=koperasi.lat, lng=koperasi.lng, label="Gudang")]
    for t in sorted(slot.tujuan, key=lambda x: x.urutan):
        penerima = db.get(Penerima, t.penerima_id)
        titik.append(Titik(lat=penerima.lat, lng=penerima.lng, label=penerima.nama if penerima else ""))

    adapter = dapatkan_adapter_vendor(db)
    kuotasi = adapter.kuotasi(titik, tier_dominan.kode)
    pesanan = adapter.pesan(kuotasi.kuotasi_id, Kontak(nama=pengguna.nama, no_hp=pengguna.no_hp))
    db.add(
        Pengiriman(
            slot_id=slot.id,
            vendor=adapter.nama,
            vendor_ref=pesanan.vendor_ref,
            status_vendor=pesanan.status,
            kuotasi_json=kuotasi.rincian,
        )
    )

    db.commit()
    db.refresh(slot)
    return _bangun_slot_detail(slot, db, pengguna)


@router.post("/{slot_id}/batal", response_model=SlotDetailOut)
def batal_slot(slot_id: UUID, pengguna=Depends(wajib_peran("KOPERASI")), db: Session = Depends(get_db)):
    slot = _slot_atau_404(db, slot_id)
    if slot.koperasi_id != pengguna.koperasi_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Slot bukan milik koperasi Anda")
    if slot.status in (StatusSlot.SELESAI, StatusSlot.BATAL):
        raise HTTPException(status.HTTP_409_CONFLICT, "Slot sudah selesai atau sudah dibatalkan")

    slot.status = StatusSlot.BATAL
    for p in slot.partisipasi:
        if p.status != StatusPartisipasi.BATAL:
            p.status = StatusPartisipasi.BATAL

    for permintaan in db.query(Permintaan).filter_by(slot_id=slot.id).all():
        permintaan.slot_id = None
        if permintaan.status not in (StatusPermintaan.TERPENUHI,):
            permintaan.status = StatusPermintaan.TERBUKA

    db.commit()
    db.refresh(slot)
    return _bangun_slot_detail(slot, db, pengguna)
