"""Layanan pencocokan kiriman → muatan (spec v2 §3/C0).

Bentuk INCREMENTAL dari algoritma greedy `app.domain.pencocokan.kelompokkan`:
kiriman baru masuk ke muatan (slot DIBUKA) yang tujuannya berada dalam radius
koridor DAN tanggalnya dalam jendela — kalau tidak ada, buka muatan baru.
Kelompok yang kelebihan kapasitas armada dipecah berdasarkan urutan
pendaftaran (§3.2 catatan): yang sudah ada tetap di muatan pertama, kiriman
baru membuka muatan kedua.
"""

import math
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Kiriman, Komoditas, Partisipasi, Penerima, Pengguna, Slot, SlotTujuan, TitikKumpul
from app.models.enums import StatusPartisipasi, StatusSlot
from app.schemas.kiriman import KirimanCreate, KirimanPratinjauResponse, KirimanResponse
from app.services import mesin
from app.services.konfigurasi import baca_konfigurasi, baca_tiers_aktif


def _jarak_haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(min(1.0, a)))


def _titik_kumpul_pengguna(db: Session, pengguna: Pengguna) -> TitikKumpul:
    if pengguna.titik_kumpul_id is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pengguna ini tidak terhubung ke titik kumpul")
    tk = db.get(TitikKumpul, pengguna.titik_kumpul_id)
    if tk is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Titik kumpul tidak ditemukan")
    return tk


def _penerima_terdekat(db: Session, lat: float, lng: float) -> tuple[Penerima | None, float]:
    """Penerima terdaftar terdekat dari titik tujuan kiriman + jaraknya (km)."""
    terdekat: Penerima | None = None
    jarak_min = float("inf")
    for p in db.query(Penerima).all():
        jarak = _jarak_haversine_km(lat, lng, p.lat, p.lng)
        if jarak < jarak_min:
            jarak_min = jarak
            terdekat = p
    return terdekat, jarak_min


def _slot_kandidat(
    db: Session,
    tk_id: UUID,
    lat_tujuan: float,
    lng_tujuan: float,
    tanggal_siap: date,
    jendela_hari: int,
    radius_koridor_km: float,
) -> list[Slot]:
    """Slot DIBUKA di titik kumpul yang sama, tanggal dalam jendela, dan salah
    satu tujuan rutenya berada dalam radius koridor dari tujuan kiriman —
    urut pendaftaran (yang daftar duluan diisi duluan, §3.2).

    Pencocokan mengukur jarak ke TITIK TUJUAN slot (koridor), bukan kesetaraan
    penerima — dua petani dengan tujuan berbeda tapi berdekatan masuk muatan
    yang sama (§8.2: Wati 8 km dari tujuan Asep)."""
    batas = timedelta(days=jendela_hari)
    slots = (
        db.query(Slot)
        .filter(
            Slot.titik_kumpul_id == tk_id,
            Slot.status == StatusSlot.DIBUKA,
            Slot.tanggal_kirim >= tanggal_siap - batas,
            Slot.tanggal_kirim <= tanggal_siap + batas,
        )
        .order_by(Slot.dibuat_pada)
        .all()
    )
    cocok: list[Slot] = []
    for s in slots:
        jarak_min = float("inf")
        for t in s.tujuan:
            p = db.get(Penerima, t.penerima_id)
            if p is not None:
                jarak_min = min(jarak_min, _jarak_haversine_km(lat_tujuan, lng_tujuan, p.lat, p.lng))
        if jarak_min <= radius_koridor_km:
            cocok.append(s)
    return cocok


def _jarak_rute_tunggal(db: Session, tk: TitikKumpul, penerima: Penerima) -> float:
    """Jarak rute satu tujuan: haversine titik kumpul → penerima × faktor_jalan."""
    faktor_jalan = baca_konfigurasi(db, "faktor_jalan")
    return _jarak_haversine_km(tk.lat, tk.lng, penerima.lat, penerima.lng) * faktor_jalan


def _harga_berjalan_slot(db: Session, slot: Slot) -> int | None:
    if slot.volume_terkunci_kg <= 0:
        return None
    tiers, maks = baca_tiers_aktif(db), baca_konfigurasi(db, "maks_kendaraan")
    try:
        rencana = mesin.rencana_armada(slot.volume_terkunci_kg, float(slot.jarak_km), tiers, maks)
    except mesin.VolumeTerlaluBesar:
        return None
    return math.ceil(rencana.biaya_total / slot.volume_terkunci_kg)


def pratinjau_kiriman(
    db: Session,
    pengguna: Pengguna,
    volume_kg: int,
    lat: float,
    lng: float,
    tanggal_siap: date,
) -> KirimanPratinjauResponse:
    """§3.4 langkah 3 — tampilkan atap + potensi SEBELUM petani berkomitmen."""
    tk = _titik_kumpul_pengguna(db, pengguna)
    radius = baca_konfigurasi(db, "radius_koridor_km")
    jendela = baca_konfigurasi(db, "jendela_hari")
    tiers, maks = baca_tiers_aktif(db), baca_konfigurasi(db, "maks_kendaraan")

    penerima, jarak = _penerima_terdekat(db, lat, lng)
    if penerima is None or jarak > radius:
        return KirimanPratinjauResponse(
            harga_atap_per_kg=None,
            harga_potensial_per_kg=None,
            slot_cocok_ada=False,
            penerima_terdekat_id=penerima.id if penerima else None,
            nama_penerima_terdekat=penerima.nama if penerima else None,
            jarak_ke_penerima_km=round(jarak, 1),
            pesan=f"Tujuan di luar koridor layanan (terdekat {jarak:.0f} km, radius {radius:.0f} km).",
        )

    jarak_rute = _jarak_rute_tunggal(db, tk, penerima)
    try:
        atap = mesin.harga_atap_per_kg(volume_kg, jarak_rute, tiers, maks)
    except (mesin.VolumeKosong, mesin.VolumeTerlaluBesar) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc))

    kandidat = _slot_kandidat(db, tk.id, lat, lng, tanggal_siap, jendela, radius)
    if kandidat:
        slot = kandidat[0]
        potensi = mesin.harga_berjalan_per_kg(slot.volume_terkunci_kg + volume_kg, float(slot.jarak_km), tiers, maks)
        cocok = True
        pesan = f"Ada muatan menuju {penerima.nama} — kamu langsung masuk muatan yang sama."
    else:
        # Proyeksi "kalau ada petani lain seukuran kamu ke arah yang sama" (§3.4).
        potensi = mesin.harga_berjalan_per_kg(volume_kg * 4, jarak_rute, tiers, maks)
        cocok = False
        pesan = "Belum ada muatan ke arah ini — muatan baru dibuka atas namamu."

    return KirimanPratinjauResponse(
        harga_atap_per_kg=atap,
        harga_potensial_per_kg=potensi,
        slot_cocok_ada=cocok,
        penerima_terdekat_id=penerima.id,
        nama_penerima_terdekat=penerima.nama,
        jarak_ke_penerima_km=round(jarak, 1),
        pesan=pesan,
    )


def buat_kiriman(db: Session, pengguna: Pengguna, body: KirimanCreate) -> KirimanResponse:
    """POST /api/kiriman — cocokkan ke muatan yang ada atau buka muatan baru (§3.5)."""
    tk = _titik_kumpul_pengguna(db, pengguna)
    if tk.kode is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Titik kumpul belum punya kode singkat (kolom `kode`)")
    komoditas = db.get(Komoditas, body.komoditas_id)
    if komoditas is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Komoditas tidak ditemukan")

    radius = baca_konfigurasi(db, "radius_koridor_km")
    jendela = baca_konfigurasi(db, "jendela_hari")
    tiers, maks = baca_tiers_aktif(db), baca_konfigurasi(db, "maks_kendaraan")

    penerima, jarak = _penerima_terdekat(db, body.lat_tujuan, body.lng_tujuan)
    if penerima is None or jarak > radius:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Tujuan di luar koridor layanan (penerima terdekat {jarak:.0f} km, radius koridor {radius:.0f} km).",
        )

    kandidat = _slot_kandidat(db, tk.id, body.lat_tujuan, body.lng_tujuan, body.tanggal_siap, jendela, radius)
    slot: Slot | None = None
    baru_dibuat = False

    for calon in kandidat:
        # Muatan yang sudah ada dipertahankan duluan — kiriman ini hanya masuk
        # kalau armada masih sanggup (§3.2 catatan pemecahan kelompok).
        try:
            mesin.rencana_armada(calon.volume_terkunci_kg + body.volume_kg, float(calon.jarak_km), tiers, maks)
        except mesin.VolumeTerlaluBesar:
            continue
        slot = calon
        break

    if slot is None:
        # Buka muatan baru satu tujuan (rute dihitung ulang dari koordinat asli).
        jarak_rute = _jarak_rute_tunggal(db, tk, penerima)
        jam_cutoff = baca_konfigurasi(db, "jam_cutoff_default")
        tanggal_kirim = body.tanggal_siap
        cutoff_at = datetime.combine(tanggal_kirim - timedelta(days=1), time(jam_cutoff - 7, 0), tzinfo=timezone.utc)
        nn = db.query(Slot).filter_by(titik_kumpul_id=tk.id, tanggal_kirim=tanggal_kirim).count() + 1
        slot = Slot(
            kode=f"SM-{tanggal_kirim:%Y%m%d}-{tk.kode}-{nn:02d}",
            titik_kumpul_id=tk.id,
            tanggal_kirim=tanggal_kirim,
            cutoff_at=cutoff_at,
            status=StatusSlot.DIBUKA,
            jarak_km=Decimal(str(round(jarak_rute, 2))),
            volume_terkunci_kg=0,
            selisih_jaminan_atap=0,
        )
        db.add(slot)
        db.flush()
        db.add(
            SlotTujuan(
                slot_id=slot.id,
                penerima_id=penerima.id,
                urutan=1,
                jarak_segmen_km=Decimal(str(round(jarak_rute, 2))),
            )
        )
        baru_dibuat = True

    jarak_slot = float(slot.jarak_km)
    try:
        atap = mesin.harga_atap_per_kg(body.volume_kg, jarak_slot, tiers, maks)
    except (mesin.VolumeKosong, mesin.VolumeTerlaluBesar) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc))

    # Jaminan atap peserta lama (§5.5) — sama seperti alur gabung klasik.
    existing = [
        mesin.PartisipasiHarga(id=p.id, volume_kg=p.volume_kg, harga_atap_per_kg=p.harga_atap_per_kg)
        for p in slot.partisipasi
        if p.status != StatusPartisipasi.BATAL
    ]
    hasil_luapan = mesin.cek_luapan_kapasitas(body.volume_kg, existing, jarak_slot, tiers, maks)
    if hasil_luapan.luapan:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Bergabung dengan {body.volume_kg} kg akan menaikkan harga berjalan ke "
            f"Rp{hasil_luapan.harga_baru_per_kg}/kg, melampaui harga atap "
            f"{hasil_luapan.jumlah_atap_terdampak} peserta yang sudah bergabung.",
        )

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
    db.flush()

    kiriman = Kiriman(
        petani_id=pengguna.id,
        komoditas_id=body.komoditas_id,
        volume_kg=body.volume_kg,
        tanggal_siap=body.tanggal_siap,
        lat_tujuan=body.lat_tujuan,
        lng_tujuan=body.lng_tujuan,
        alamat_tujuan=body.alamat_tujuan,
        slot_id=slot.id,
        partisipasi_id=partisipasi.id,
    )
    db.add(kiriman)
    db.commit()

    # Query segar pasca-commit (relasi slot.partisipasi bisa sudah ter-cache
    # sebelum partisipasi baru ditambahkan).
    jumlah_peserta = len(
        {
            p.petani_id
            for p in db.query(Partisipasi).filter(
                Partisipasi.slot_id == slot.id, Partisipasi.status != StatusPartisipasi.BATAL
            )
        }
    )
    return KirimanResponse(
        slot_id=slot.id,
        harga_atap_per_kg=atap,
        harga_berjalan_per_kg=_harga_berjalan_slot(db, slot),
        jumlah_peserta=jumlah_peserta,
        baru_dibuat=baru_dibuat,
    )
