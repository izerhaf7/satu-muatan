"""Endpoint pelacakan (§9.6) + telemetri suhu/kelembapan (spec v2 §5/C2)."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_pengguna_aktif, wajib_peran
from app.database import get_db
from app.domain.armada import jarak_haversine_km
from app.domain.paparan import SampelTelemetri, hitung_paparan
from app.domain.rute_polyline import decode_polyline, panjang_polyline_km, posisi_pada_polyline
from app.models import JejakPosisi, Komoditas, Lot, Partisipasi, Penerima, Pengiriman, Slot, TitikKumpul
from app.models.enums import StatusPartisipasi, StatusSlot, SumberPosisi
from app.schemas.lacak import (
    PengirimanOut,
    PerjalananResiOut,
    PosisiOut,
    SampaiRequest,
    TelemetriOut,
    TelemetriRingkasanOut,
    TelemetriSampelOut,
    TimelineOut,
    TitikPetaOut,
)
from app.services import mesin
from app.services.konfigurasi import baca_konfigurasi
from app.services.otorisasi import pastikan_bisa_lihat_slot, pastikan_petugas_muatan
from app.services.telemetri import pastikan_telemetri

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
    # T5: kalau provider rute memberi durasi (Google/haversine), estimasi tiba
    # memakai durasi itu; kalau tidak, jatuh ke ambang transit (jarak/kecepatan).
    if pengiriman.rute_durasi_provider_menit is not None and pengiriman.waktu_berangkat is not None:
        estimasi_tiba = pengiriman.waktu_berangkat + timedelta(minutes=pengiriman.rute_durasi_provider_menit)
    else:
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
        eta_provider_menit=pengiriman.rute_durasi_provider_menit,
        jarak_provider_km=(
            float(pengiriman.rute_jarak_provider_km) if pengiriman.rute_jarak_provider_km is not None else None
        ),
        jejak=[PosisiOut(lat=j.lat, lng=j.lng, waktu=j.waktu, sumber=j.sumber) for j in jejak],
        rute_polyline=pengiriman.rute_polyline,
        rute_versi=pengiriman.rute_versi,
        eta_sumber=pengiriman.rute_sumber,
        eta_dihitung_pada=pengiriman.rute_dihitung_pada,
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


@router.get("/lacak/{slot_id}/telemetri", response_model=TelemetriOut)
def telemetri_slot(slot_id: UUID, pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    """Sampel telemetri + ringkasan paparan (§5.3). Lazy-generate deterministik
    saat pertama dipanggil (SIMULASI, berlabel di UI)."""
    slot = db.get(Slot, slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Slot tidak ditemukan")
    pastikan_bisa_lihat_slot(pengguna, slot)
    pengiriman = db.query(Pengiriman).filter_by(slot_id=slot.id).one_or_none()
    if pengiriman is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Slot ini belum punya pengiriman (belum ditutup)")
    return _telemetri_out(db, slot, pengiriman)


@router.get("/lacak/resi/{kode_resi}", response_model=PerjalananResiOut)
def perjalanan_resi(kode_resi: str, pengguna=Depends(wajib_peran("PENERIMA")), db: Session = Depends(get_db)):
    """K14: seluruh perjalanan satu resi — timeline, jejak posisi, dan telemetri.

    Otorisasinya RESI, bukan alamat. `pastikan_bisa_lihat_slot` untuk penerima
    masih membandingkan `pengguna.penerima_id` dengan tujuan muatan, dan K13
    membuat tujuan bebas — jadi jalur itu tidak lagi bisa dipakai penerima yang
    sah. Memegang nomor resi adalah buktinya, persis seperti surat jalan."""
    lot = db.query(Lot).filter_by(kode_qr=kode_resi).one_or_none()
    if lot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nomor resi tidak ditemukan")

    partisipasi = db.get(Partisipasi, lot.partisipasi_id)
    slot = db.get(Slot, partisipasi.slot_id) if partisipasi else None
    pengiriman = db.query(Pengiriman).filter_by(slot_id=slot.id).one_or_none() if slot else None
    if slot is None or pengiriman is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resi ini belum punya pengiriman")

    return PerjalananResiOut(
        pengiriman=_ke_pengiriman_out(pengiriman, slot, db),
        telemetri=_telemetri_out(db, slot, pengiriman),
        titik_kumpul=_titik_kumpul_out(db, slot),
        tujuan=_tujuan_out(db, slot),
    )


def _titik_kumpul_out(db: Session, slot: Slot) -> TitikPetaOut:
    tk = db.get(TitikKumpul, slot.titik_kumpul_id)
    return TitikPetaOut(nama=tk.nama if tk else "Titik kumpul", lat=tk.lat if tk else 0.0, lng=tk.lng if tk else 0.0)


def _tujuan_out(db: Session, slot: Slot) -> list[TitikPetaOut]:
    hasil = []
    for t in sorted(slot.tujuan, key=lambda x: x.urutan):
        p = db.get(Penerima, t.penerima_id)
        if p is not None:
            hasil.append(TitikPetaOut(nama=p.nama, lat=p.lat, lng=p.lng))
    return hasil


def _telemetri_out(db: Session, slot: Slot, pengiriman: Pengiriman) -> TelemetriOut:
    baris = pastikan_telemetri(db, pengiriman, slot)
    sampel_out = [
        TelemetriSampelOut(
            waktu=r.waktu,
            suhu_c=float(r.suhu_c),
            kelembapan_persen=float(r.kelembapan_persen),
            lat=r.lat,
            lng=r.lng,
            sumber=r.sumber,
        )
        for r in baris
    ]
    if not baris:
        return TelemetriOut(sampel=[], ringkasan=None)

    # Komoditas dominan by volume — basis parameter Q10/umur simpan ringkasan.
    volume_per_komoditas: dict[UUID, int] = {}
    for p in slot.partisipasi:
        if p.status != StatusPartisipasi.BATAL:
            volume_per_komoditas[p.komoditas_id] = volume_per_komoditas.get(p.komoditas_id, 0) + p.volume_kg
    komoditas = None
    if volume_per_komoditas:
        komoditas_id = max(volume_per_komoditas, key=lambda item: volume_per_komoditas[item])
        komoditas = db.get(Komoditas, komoditas_id)

    sampel_domain = []
    waktu_sebelumnya = None
    for r in baris:
        menit = 0 if waktu_sebelumnya is None else int((r.waktu - waktu_sebelumnya).total_seconds() // 60)
        sampel_domain.append(
            SampelTelemetri(suhu_c=float(r.suhu_c), kelembapan_persen=float(r.kelembapan_persen), menit_sejak_sebelumnya=menit)
        )
        waktu_sebelumnya = r.waktu

    q10 = float(komoditas.q10) if komoditas else 2.0
    suhu_acuan = float(komoditas.suhu_acuan_c) if komoditas else 25.0
    umur = komoditas.umur_simpan_jam if komoditas else 72
    hasil = hitung_paparan(sampel_domain, q10, suhu_acuan, umur)
    kelembapan_rata = round(sum(float(r.kelembapan_persen) for r in baris) / len(baris), 2)

    return TelemetriOut(
        sampel=sampel_out,
        ringkasan=TelemetriRingkasanOut(
            suhu_maks_c=round(hasil.suhu_maks_c, 2),
            suhu_rata_c=round(hasil.suhu_rata_c, 2),
            kelembapan_rata_persen=kelembapan_rata,
            jam_ekivalen=round(hasil.jam_ekivalen, 2),
            sisa_umur_simpan_persen=hasil.sisa_umur_simpan_persen,
            suhu_acuan_c=suhu_acuan,
            nama_komoditas=komoditas.nama if komoditas else None,
        ),
    )


@router.post("/pengiriman/{pengiriman_id}/majukan", response_model=PengirimanOut)
def majukan_pengiriman(pengiriman_id: UUID, pengguna=Depends(wajib_peran("PETUGAS")), db: Session = Depends(get_db)):
    """Majukan state simulasi MockVendor satu langkah (K5) — deterministik, untuk demo."""
    pengiriman = db.get(Pengiriman, pengiriman_id)
    if pengiriman is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pengiriman tidak ditemukan")
    slot = db.get(Slot, pengiriman.slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Muatan tidak ditemukan")
    pastikan_petugas_muatan(pengguna, slot)

    # T7: muatan harus sudah berangkat (slot JALAN) sebelum boleh dimajukan —
    # mencegah lacak/majukan sebelum muat selesai.
    if slot.status != StatusSlot.JALAN:
        raise HTTPException(status.HTTP_409_CONFLICT, "MUAT_BELUM_SELESAI")

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


def _rute_titik(db: Session, slot: Slot) -> list[tuple[float, float]]:
    """Titik rute rencana: titik kumpul, semua jemput, lalu semua tujuan."""
    titik_kumpul = db.get(TitikKumpul, slot.titik_kumpul_id)
    titik: list[tuple[float, float]] = []
    if titik_kumpul is not None:
        titik.append((titik_kumpul.lat, titik_kumpul.lng))
    for jemput in sorted(slot.jemput, key=lambda x: x.urutan):
        titik.append((jemput.lat, jemput.lng))
    for t in sorted(slot.tujuan, key=lambda x: x.urutan):
        penerima = db.get(Penerima, t.penerima_id)
        if penerima is not None:
            titik.append((penerima.lat, penerima.lng))
    return titik


@router.post("/pengiriman/{pengiriman_id}/geser", response_model=PengirimanOut)
def geser_posisi(pengiriman_id: UUID, pengguna=Depends(wajib_peran("PETUGAS")), db: Session = Depends(get_db)):
    """K13: majukan POSISI kendaraan sepanjang rute, bukan status.

    T6: gerak KONTINU sepanjang polyline, dikompresi waktu. Posisi dihitung dari
    jarak yang ditempuh = kecepatan × (waktu berjalan × percepatan simulasi),
    lalu diinterpolasi di sepanjang polyline (klamp di kedua ujung). Tiap
    panggilan menulis satu titik `JejakPosisi`; begitu jarak tempuh melewati
    panjang polyline, muatan ditandai TIBA. Dipakai tombol "Majukan posisi" dan
    mode "jalan otomatis" di layar Lacak."""
    pengiriman = db.get(Pengiriman, pengiriman_id)
    if pengiriman is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pengiriman tidak ditemukan")
    slot = db.get(Slot, pengiriman.slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Muatan tidak ditemukan")
    pastikan_petugas_muatan(pengguna, slot)
    if pengiriman.waktu_berangkat is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Muatan belum berangkat")
    # T7: muatan harus sudah berangkat (slot JALAN) sebelum boleh digeser —
    # mencegah lacak sebelum muat selesai.
    if slot.status != StatusSlot.JALAN:
        raise HTTPException(status.HTTP_409_CONFLICT, "MUAT_BELUM_SELESAI")
    if pengiriman.waktu_tiba is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Muatan sudah tiba")

    # Rute: decode polyline provider; kalau rusak/kosong, jatuh ke rantai garis
    # lurus `_rute_titik` (titik kumpul → jemput → tujuan).
    polyline: list[tuple[float, float]] = []
    if pengiriman.rute_polyline:
        try:
            polyline = decode_polyline(pengiriman.rute_polyline)
        except ValueError:
            polyline = []
    if len(polyline) < 2:
        polyline = _rute_titik(db, slot)
    if len(polyline) < 2:
        # Tidak ada rute yang bisa dijadikan posisi — pertahankan titik awal.
        lat, lng = (0.0, 0.0)
    else:
        panjang = panjang_polyline_km(polyline)
        elapsed_menit = max((datetime.now(timezone.utc) - pengiriman.waktu_berangkat).total_seconds() / 60, 0.0)
        percepatan = float(baca_konfigurasi(db, "simulasi_percepatan_x"))
        kecepatan = float(baca_konfigurasi(db, "kecepatan_rata_kmh"))
        jarak_tempuh_km = kecepatan * (elapsed_menit * percepatan) / 60
        lat, lng = posisi_pada_polyline(polyline, jarak_tempuh_km)

    sekarang = datetime.now(timezone.utc)
    db.add(
        JejakPosisi(
            pengiriman_id=pengiriman.id,
            lat=lat,
            lng=lng,
            waktu=sekarang,
            sumber=SumberPosisi.SIMULASI,
        )
    )

    if len(polyline) < 2 or jarak_tempuh_km >= panjang:
        pengiriman.waktu_tiba = sekarang
        pengiriman.status_vendor = "TIBA"
    else:
        pengiriman.status_vendor = "JALAN"

    db.commit()
    db.refresh(pengiriman)
    return _ke_pengiriman_out(pengiriman, slot, db)


@router.post("/pengiriman/{pengiriman_id}/sampai", response_model=PengirimanOut)
def sampai_pengiriman(
    pengiriman_id: UUID,
    body: SampaiRequest | None = None,
    pengguna=Depends(wajib_peran("PETUGAS")),
    db: Session = Depends(get_db),
):
    """T8: petugas menyatakan muatan tiba di tujuan akhir.

    Body opsional: kalau `koordinat` GPS petugas diberikan, kedatangan hanya
    diterima kalau koordinat itu berada dalam `radius_sampai_m` dari tujuan
    akhir (titik drop terakhir). Tanpa koordinat, kedatangan diterima begitu
    saja. Idempoten: muatan yang sudah tiba ditolak 409."""
    pengiriman = db.get(Pengiriman, pengiriman_id)
    if pengiriman is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pengiriman tidak ditemukan")
    slot = db.get(Slot, pengiriman.slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Muatan tidak ditemukan")
    pastikan_petugas_muatan(pengguna, slot)
    if slot.status != StatusSlot.JALAN:
        raise HTTPException(status.HTTP_409_CONFLICT, "MUAT_BELUM_SELESAI")
    if pengiriman.waktu_tiba is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "SUDAH_TIBA")

    # Tujuan akhir = titik drop terakhir dari rute rencana.
    titik = _rute_titik(db, slot)
    if not titik:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Muatan tidak punya rute tujuan")
    tujuan = titik[-1]

    if body is not None and body.koordinat is not None:
        jarak_m = jarak_haversine_km(body.koordinat.lat, body.koordinat.lng, tujuan[0], tujuan[1]) * 1000
        radius_sampai_m = float(baca_konfigurasi(db, "radius_sampai_m"))
        if jarak_m > radius_sampai_m:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "BELUM_DI_TUJUAN")

    sekarang = datetime.now(timezone.utc)
    pengiriman.waktu_tiba = sekarang
    pengiriman.status_vendor = "TIBA"
    db.add(
        JejakPosisi(
            pengiriman_id=pengiriman.id,
            lat=tujuan[0],
            lng=tujuan[1],
            waktu=sekarang,
            sumber=SumberPosisi.SIMULASI,
        )
    )

    db.commit()
    db.refresh(pengiriman)
    return _ke_pengiriman_out(pengiriman, slot, db)
