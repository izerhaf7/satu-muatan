"""Endpoint lot: muat (§9.5), bukti QR & serah terima (§9.7)."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_pengguna_aktif, wajib_peran
from app.database import get_db
from app.models import (
    JejakPosisi,
    Komoditas,
    Lot,
    Partisipasi,
    Penerima,
    Pengguna,
    Pengiriman,
    SerahTerima,
    Slot,
    TitikKumpul,
)
from app.models.enums import (
    Atribusi,
    KeputusanSerahTerima,
    StatusPartisipasi,
    StatusPengiriman,
    StatusSlot,
    SumberPosisi,
)
from app.schemas.lot import (
    BuktiLotOut,
    IndeksMutuOut,
    LotOut,
    MuatPatchRequest,
    SerahTerimaCreate,
    SerahTerimaOut,
)
from app.services import mesin
from app.services.konfigurasi import baca_konfigurasi
from app.services.otorisasi import pastikan_bisa_lihat_slot, pastikan_petugas_muatan
from app.services.telemetri import sisa_umur_simpan_persen

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
        slot_id=partisipasi.slot_id if partisipasi else None,
        nama_petani=petani.nama if petani else "",
        nama_komoditas=komoditas.nama if komoditas else "",
        volume_kg=partisipasi.volume_kg if partisipasi else 0,
        penerima_id=lot.penerima_id,
        nama_penerima=penerima.nama if penerima else None,
        berat_aktual_kg=lot.berat_aktual_kg,
        foto_muat=lot.foto_muat,
        waktu_muat=lot.waktu_muat,
        catatan_muat=lot.catatan_muat,
        grade_asal=lot.grade_asal,
    )


_LABEL_GRADE = {5: "Sangat baik", 4: "Baik", 3: "Cukup", 2: "Kurang", 1: "Tidak layak"}


def _bangun_penjelasan(
    atribusi: str,
    durasi_menit: int,
    ambang_menit: int,
    grade_asal: int | None,
    grade_tiba: int | None,
    sisa_persen: int | None,
    ambang_paparan: int,
) -> str:
    """Kalimat penjelasan (spec v2 §6.3) — bukan cuma label."""
    asal = _LABEL_GRADE.get(grade_asal or 5, "Sangat baik")
    tiba = _LABEL_GRADE.get(grade_tiba or 5, "Sangat baik")
    sisa_teks = sisa_persen if sisa_persen is not None else 100

    if atribusi == Atribusi.PETANI.value:
        return f"Mutu saat muat sudah di bawah standar ({asal}), sebelum barang berangkat."
    if atribusi == Atribusi.NORMAL.value:
        return "Tidak ada penurunan mutu."
    if atribusi == Atribusi.LOGISTIK.value:
        if durasi_menit > ambang_menit:
            bukti = f"Waktu tempuh {durasi_menit} menit melewati ambang {ambang_menit} menit untuk rute ini."
        else:
            bukti = f"Sisa umur simpan {sisa_teks}% di bawah ambang wajar {ambang_paparan}%."
        return f"Mutu turun dari {asal} ke {tiba}. {bukti}"
    return (
        f"Mutu turun dari {asal} ke {tiba}, tetapi waktu tempuh {durasi_menit} menit masih di dalam "
        f"ambang {ambang_menit} menit dan sisa umur simpan {sisa_teks}% masih wajar. "
        "Penyebabnya tidak terekam sistem."
    )


def _ke_serah_terima_out(st: SerahTerima, lot: Lot, db: Session) -> SerahTerimaOut:
    ambang_paparan = baca_konfigurasi(db, "ambang_paparan_persen")
    penjelasan = _bangun_penjelasan(
        st.atribusi.value,
        st.durasi_transit_menit,
        st.ambang_transit_menit,
        lot.grade_asal,
        st.grade_tiba,
        st.sisa_umur_simpan_persen,
        ambang_paparan,
    )
    return SerahTerimaOut(
        id=st.id,
        lot_id=st.lot_id,
        penerima_id=st.penerima_id,
        waktu_bongkar=st.waktu_bongkar,
        keputusan=st.keputusan,
        alasan=st.alasan,
        durasi_transit_menit=st.durasi_transit_menit,
        ambang_transit_menit=st.ambang_transit_menit,
        atribusi=st.atribusi,
        penjelasan=penjelasan,
        foto_bongkar=st.foto_bongkar,  # K10
        grade_asal=lot.grade_asal,
        grade_tiba=st.grade_tiba,
        sisa_umur_simpan_persen=st.sisa_umur_simpan_persen,
        indeks_mutu=st.indeks_mutu,
    )


def _ambang_slot(db: Session, slot: Slot) -> int:
    kecepatan = baca_konfigurasi(db, "kecepatan_rata_kmh")
    toleransi = baca_konfigurasi(db, "faktor_toleransi_transit")
    return mesin.ambang_transit_menit(float(slot.jarak_km), kecepatan, toleransi)


def _nilai_mutu(
    db: Session, lot: Lot, slot: Slot | None, pengiriman: Pengiriman | None, durasi_menit: int | None
) -> tuple[mesin.HasilIndeksMutu, int | None]:
    """K14: penilaian mutu SISTEM. Mengembalikan hasil + sisa umur simpan mentah.

    Dipakai dua kali dan HARUS sama persis: sekali untuk ditampilkan sebelum
    keputusan, sekali untuk menjaga tombol Tolak di server. Kalau keduanya
    dihitung terpisah, penerima bisa melihat satu angka lalu dinilai dengan
    angka lain."""
    partisipasi = db.get(Partisipasi, lot.partisipasi_id)
    komoditas = db.get(Komoditas, partisipasi.komoditas_id) if partisipasi else None
    sisa = (
        sisa_umur_simpan_persen(db, pengiriman, slot, komoditas)
        if (pengiriman is not None and slot is not None)
        else None
    )
    # Tanpa sampel telemetri, umur simpan dianggap utuh — sama seperti atribusi,
    # supaya ketiadaan data tidak berubah jadi tuduhan.
    hasil = mesin.hitung_indeks_mutu(
        sisa_umur_simpan_persen=sisa if sisa is not None else 100,
        durasi_transit_menit=durasi_menit or 0,
        ambang_transit_menit=_ambang_slot(db, slot) if slot else 0,
        bobot_umur_simpan=baca_konfigurasi(db, "bobot_mutu_umur_simpan"),
        bobot_transit=baca_konfigurasi(db, "bobot_mutu_transit"),
        ambang_tolak_persen=baca_konfigurasi(db, "ambang_tolak_persen"),
    )
    return hasil, sisa


def _mutu_out(db: Session, hasil: mesin.HasilIndeksMutu, sisa: int | None) -> IndeksMutuOut:
    ambang_tolak = baca_konfigurasi(db, "ambang_tolak_persen")
    if hasil.boleh_tolak:
        alasan = (
            f"Penurunan mutu terukur {hasil.penurunan_mutu_persen}% melewati ambang {ambang_tolak}% — "
            "barang boleh ditolak."
        )
    else:
        alasan = (
            f"Penurunan mutu terukur {hasil.penurunan_mutu_persen}%, masih di bawah ambang {ambang_tolak}%. "
            "Barang harus diterima; keberatan mutu tetap tercatat lewat grade tiba dan atribusi."
        )
    return IndeksMutuOut(
        indeks_mutu=hasil.indeks_mutu,
        penurunan_mutu_persen=hasil.penurunan_mutu_persen,
        skor_umur_simpan=hasil.skor_umur_simpan,
        skor_transit=hasil.skor_transit,
        sisa_umur_simpan_persen=sisa,
        boleh_tolak=hasil.boleh_tolak,
        ambang_tolak_persen=ambang_tolak,
        alasan_boleh_tolak=alasan,
    )


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

    hasil, sisa = _nilai_mutu(db, lot, slot, pengiriman, durasi_berjalan)

    st = db.query(SerahTerima).filter_by(lot_id=lot.id).one_or_none()
    return BuktiLotOut(
        lot=lot_out,
        durasi_transit_berjalan_menit=durasi_berjalan,
        ambang_transit_menit=ambang,
        mutu=_mutu_out(db, hasil, sisa),
        serah_terima=_ke_serah_terima_out(st, lot, db) if st is not None else None,
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
def muat_lot(lot_id: UUID, body: MuatPatchRequest, pengguna=Depends(wajib_peran("PETUGAS")), db: Session = Depends(get_db)):
    """Timbang + foto + grade mutu 1–5 (input kunci atribusi 3-input, spec v2 §6)."""
    lot = _lot_atau_404(db, lot_id)
    partisipasi = db.get(Partisipasi, lot.partisipasi_id)
    slot = db.get(Slot, partisipasi.slot_id) if partisipasi else None
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Muatan tidak ditemukan")
    pastikan_petugas_muatan(pengguna, slot)
    if slot.status not in (StatusSlot.TERKUNCI, StatusSlot.DIMUAT):
        raise HTTPException(status.HTTP_409_CONFLICT, "Slot tidak dalam tahap pemuatan")

    # K14: FOTO MUAT WAJIB. Petugas adalah penghubung yang menyaksikan barang
    # berpindah tangan; tanpa fotonya, Berita Acara dan Serah Terima kehilangan
    # satu-satunya bukti visual kondisi barang saat berangkat — dan atribusi
    # mutu jadi klaim tanpa sandaran. Foto lama dipertahankan kalau permintaan
    # ini hanya mengoreksi berat.
    foto = body.foto_muat_base64 or lot.foto_muat
    if not foto:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Foto muat wajib — bukti kondisi barang saat berangkat.",
        )

    lot.berat_aktual_kg = body.berat_aktual_kg
    lot.foto_muat = foto
    lot.grade_asal = body.grade_asal
    lot.catatan_muat = body.catatan_muat
    lot.waktu_muat = datetime.now(timezone.utc)

    if slot.status == StatusSlot.TERKUNCI:
        slot.status = StatusSlot.DIMUAT

    db.commit()
    db.refresh(lot)
    return _ke_lot_out(lot, db)


@router.post("/slot/{slot_id}/selesai-muat", response_model=list[LotOut])
def selesai_muat(slot_id: UUID, pengguna=Depends(wajib_peran("PETUGAS")), db: Session = Depends(get_db)):
    """Selesai muat -> slot JALAN, waktu berangkat tercatat (§9.5)."""
    slot = db.get(Slot, slot_id)
    if slot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Muatan tidak ditemukan")
    pastikan_petugas_muatan(pengguna, slot)
    if slot.status not in (StatusSlot.TERKUNCI, StatusSlot.DIMUAT):
        raise HTTPException(status.HTTP_409_CONFLICT, "Slot tidak dalam tahap pemuatan")

    partisipasi_ids = [p.id for p in slot.partisipasi if p.status != StatusPartisipasi.BATAL]
    lots = db.query(Lot).filter(Lot.partisipasi_id.in_(partisipasi_ids)).all() if partisipasi_ids else []
    if not lots or any(lot.waktu_muat is None for lot in lots):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Semua lot wajib ditimbang sebelum selesai muat")

    # K14: penjagaan kedua — sebutkan lot mana yang belum berfoto, jangan cuma
    # menolak. Petugas sedang berdiri di truk; dia butuh tahu harus ke mana.
    tanpa_foto = [lot for lot in lots if not lot.foto_muat]
    if tanpa_foto:
        nama_lot: list[str] = []
        for lot in tanpa_foto:
            partisipasi = db.get(Partisipasi, lot.partisipasi_id)
            petani = db.get(Pengguna, partisipasi.petani_id) if partisipasi is not None else None
            nama_lot.append(petani.nama if petani is not None else "?")
        nama = ", ".join(nama_lot)
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Foto muat belum ada untuk lot: {nama}. Semua lot wajib difoto sebelum berangkat.",
        )

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
        # K13: catat titik jejak PERTAMA di titik kumpul. Sebelumnya keberangkatan
        # melompati state machine sehingga `jejak` tetap kosong dan peta tidak
        # pernah bergerak sampai tiba.
        titik_kumpul = db.get(TitikKumpul, slot.titik_kumpul_id)
        if titik_kumpul is not None:
            db.add(
                JejakPosisi(
                    pengiriman_id=pengiriman.id,
                    lat=titik_kumpul.lat,
                    lng=titik_kumpul.lng,
                    waktu=sekarang,
                    sumber=SumberPosisi.SIMULASI,
                )
            )

    db.commit()
    return [_ke_lot_out(lot, db) for lot in lots]


# ---------------------------------------------------------------------------
# Endpoint — Serah Terima (§9.7)
# ---------------------------------------------------------------------------


@router.get("/lot/masuk", response_model=list[BuktiLotOut])
def lot_masuk(pengguna=Depends(wajib_peran("PENERIMA")), db: Session = Depends(get_db)):
    """'Pilih dari daftar' (§9.7) — kenyamanan untuk akun penerima yang masih
    terikat satu alamat tetap (data seed), dibatasi ke alamat itu.

    Akun TANPA ikatan (penerima_id kosong — kini juga dicapai oleh pendaftaran
    mandiri, bukan cuma data seed lama) TIDAK melihat daftar apa pun di sini.
    Kepemilikan sungguhan ditentukan oleh nomor resi (lihat `bukti_lot`) —
    "lihat semua lot yang sedang jalan" bukan jalur akses yang aman untuk akun
    yang tidak punya hubungan apa pun dengan kirimannya."""
    if pengguna.penerima_id is None:
        return []
    q = (
        db.query(Lot)
        .join(Partisipasi, Partisipasi.id == Lot.partisipasi_id)
        .join(Slot, Slot.id == Partisipasi.slot_id)
        .filter(Slot.status.in_([StatusSlot.JALAN, StatusSlot.SELESAI]))
        .filter(Lot.penerima_id == pengguna.penerima_id)
    )
    lots = q.all()
    hasil = []
    for lot in lots:
        if db.query(SerahTerima).filter_by(lot_id=lot.id).one_or_none() is not None:
            continue
        hasil.append(_bukti_lot_out(lot, db))
    return hasil


@router.get("/lot/qr/{kode_qr}", response_model=BuktiLotOut)
def bukti_lot(kode_qr: str, pengguna=Depends(wajib_peran("PENERIMA")), db: Session = Depends(get_db)):
    """Bukti lot dari NOMOR RESI: foto muat, berat, waktu, transit berjalan vs ambang.

    K13: tidak ada lagi cek `lot.penerima_id == pengguna.penerima_id`. Tujuan kini
    bebas ditulis petani, jadi penerima tidak terikat satu alamat tetap —
    memegang nomor resi itu sendiri yang menjadi bukti berhak, persis seperti
    surat jalan sungguhan."""
    lot = db.query(Lot).filter_by(kode_qr=kode_qr).one_or_none()
    if lot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nomor resi tidak ditemukan")
    return _bukti_lot_out(lot, db)


@router.post("/lot/{lot_id}/serah-terima", response_model=SerahTerimaOut, status_code=201)
def serah_terima(
    lot_id: UUID, body: SerahTerimaCreate, pengguna=Depends(wajib_peran("PENERIMA")), db: Session = Depends(get_db)
):
    """Terima / Tolak -> atribusi + PENJELASAN (§6, §9.7).

    K13: berhak menerima = memegang nomor resinya (lihat `bukti_lot`).
    K14: tidak ada lagi "terima dengan potongan", dan TOLAK hanya sah kalau
    penurunan mutu yang DIUKUR SISTEM melewati ambang. Aturan itu ditegakkan di
    sini, bukan cuma disembunyikan tombolnya — klien tidak boleh dipercaya.

    Kontrak IoT: sesudah status pengiriman BONGKAR_MUAT, serah-terima penerima
    dengan atribusi menjadi penyelesaian final pengiriman. Driver tidak menutup
    pengiriman sendiri."""
    lot = _lot_atau_404(db, lot_id)
    if db.query(SerahTerima).filter_by(lot_id=lot.id).one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Lot ini sudah diserahterimakan")

    partisipasi = db.get(Partisipasi, lot.partisipasi_id)
    slot = db.get(Slot, partisipasi.slot_id) if partisipasi else None
    pengiriman = db.query(Pengiriman).filter_by(slot_id=slot.id).one_or_none() if slot else None
    if slot is None or pengiriman is None or pengiriman.waktu_berangkat is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Pengiriman belum berangkat")
    if pengiriman.status_pengiriman != StatusPengiriman.BONGKAR_MUAT:
        raise HTTPException(status.HTTP_409_CONFLICT, "Penerima baru dapat menyelesaikan setelah BONGKAR_MUAT")

    sekarang = datetime.now(timezone.utc)
    durasi_transit_menit = max(0, int((sekarang - pengiriman.waktu_berangkat).total_seconds() // 60))
    ambang_menit = _ambang_slot(db, slot)

    # K14: gerbang TOLAK — dihitung ulang di server dengan fungsi yang sama
    # persis dengan yang dipakai menampilkan angkanya ke penerima.
    mutu, sisa_persen = _nilai_mutu(db, lot, slot, pengiriman, durasi_transit_menit)
    if body.keputusan == KeputusanSerahTerima.TOLAK and not mutu.boleh_tolak:
        ambang_tolak = baca_konfigurasi(db, "ambang_tolak_persen")
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Barang tidak boleh ditolak: penurunan mutu terukur {mutu.penurunan_mutu_persen}%, "
            f"masih di bawah ambang {ambang_tolak}%.",
        )

    # Atribusi 3-input (spec v2 §6.2): grade asal vs grade tiba + bukti paparan
    # (transit lewat ambang ATAU sisa umur simpan terkikis).
    ambang_grade = baca_konfigurasi(db, "ambang_grade_asal")
    ambang_paparan = baca_konfigurasi(db, "ambang_paparan_persen")
    # Tanpa sampel telemetri: anggap penuh (100%) supaya cabang paparan tidak keliru aktif.
    sisa_untuk_atribusi = sisa_persen if sisa_persen is not None else 100
    atribusi_str = mesin.tentukan_atribusi(
        lot.grade_asal,
        body.grade_tiba,
        durasi_transit_menit,
        ambang_menit,
        sisa_untuk_atribusi,
        ambang_grade,
        ambang_paparan,
    )

    st = SerahTerima(
        lot_id=lot.id,
        # K13: tujuan lot itu sendiri, bukan alamat tetap milik akun penerima
        # (akun tidak lagi terikat satu alamat).
        penerima_id=lot.penerima_id or pengguna.penerima_id,
        waktu_bongkar=sekarang,
        foto_bongkar=body.foto_bongkar_base64,
        keputusan=body.keputusan,
        alasan=body.alasan,
        durasi_transit_menit=durasi_transit_menit,
        ambang_transit_menit=ambang_menit,
        atribusi=Atribusi(atribusi_str),
        grade_tiba=body.grade_tiba,
        sisa_umur_simpan_persen=sisa_untuk_atribusi,
        indeks_mutu=mutu.indeks_mutu,
    )
    db.add(st)

    if partisipasi is not None:
        # K14: penolakan bukan "selesai". Riwayat petani harus menyebut apa yang
        # sungguh terjadi pada barangnya.
        partisipasi.status = (
            StatusPartisipasi.DITOLAK
            if body.keputusan == KeputusanSerahTerima.TOLAK
            else StatusPartisipasi.SELESAI
        )

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
        pengiriman.status_pengiriman = StatusPengiriman.SELESAI

    db.commit()
    db.refresh(st)
    return _ke_serah_terima_out(st, lot, db)
