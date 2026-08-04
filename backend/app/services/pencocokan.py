"""Layanan pencocokan kiriman → muatan (spec v2 §3/C0, direvisi K13).

Bentuk INCREMENTAL dari algoritma greedy `app.domain.pencocokan.kelompokkan`:
kiriman baru masuk ke muatan (slot DIBUKA) yang tujuannya berada dalam radius
koridor DAN tanggalnya dalam jendela — kalau tidak ada, buka muatan baru.

Perubahan K13:
- **Tujuan bebas.** Petani menaruh titik tujuan sendiri; sistem memakai ulang
  alamat yang sudah dikenal kalau cukup dekat, atau membuat baris baru. Tidak
  ada lagi "snap ke penerima terdaftar terdekat" dan penolakan koridor 15 km.
- **Tujuan peserta baru benar-benar masuk rute.** Sebelumnya kiriman yang
  bergabung tidak pernah menambah `SlotTujuan`, sehingga barangnya diam-diam
  diantar ke alamat orang lain dan `jarak_km` tidak pernah dihitung ulang.
- **Bergabung tidak boleh merugikan yang sudah ada.** Kalau menggabungkan
  kiriman ini membuat harga berjalan grup NAIK (lompatan tier armada / rute
  jadi jauh), muatan itu dilewati dan muatan baru dibuka — bukan ditolak 409.
- **Volume minimal**, jadwal, dan penugasan driver ditentukan sistem.

Perubahan K14:
- **Cutoff tidak pernah lahir di masa lalu.** Muatan yang baru dibuka selalu
  memberi jeda minimal kepada petani lain untuk ikut, sehingga hitung mundur di
  layar tidak langsung berbunyi nol.
- **Muatan lewat cutoff berhenti menerima kiriman.** Sebelumnya cutoff hanya
  hiasan: slot kedaluwarsa masih menyerap kiriman baru tanpa batas.
- **Simulasi pratinjau memakai rute yang benar.** Tujuan calon dulu hilang dari
  simulasi (id-nya `None`), jadi harga yang dijanjikan bisa jauh lebih murah
  daripada yang benar-benar didapat petani.
"""

import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.armada import TujuanInput
from app.models import (
    Kiriman,
    Komoditas,
    Partisipasi,
    Penerima,
    Pengguna,
    Slot,
    SlotJemput,
    SlotTujuan,
    TitikKumpul,
)
from app.models.enums import PeranPengguna, StatusPartisipasi, StatusSlot, TipePenerima
from app.schemas.kiriman import KirimanCreate, KirimanPratinjauResponse, KirimanResponse
from app.services import mesin
from app.services.konfigurasi import baca_konfigurasi, baca_tiers_aktif

# Status muatan yang masih membebani seorang driver (dipakai penugasan otomatis).
STATUS_MUATAN_AKTIF = (StatusSlot.DIBUKA, StatusSlot.TERKUNCI, StatusSlot.DIMUAT, StatusSlot.JALAN)


def sekarang_utc() -> datetime:
    """Satu-satunya sumber "sekarang" di layanan ini — supaya test bisa
    membandingkan dan `app/domain/` tetap murni (CLAUDE.md aturan #2)."""
    return datetime.now(timezone.utc)


def _aware(waktu: datetime) -> datetime:
    """Kolom `cutoff_at` bisa kembali naive dari SQLite di test; samakan dulu
    sebelum dibandingkan supaya tidak melempar TypeError."""
    return waktu if waktu.tzinfo is not None else waktu.replace(tzinfo=timezone.utc)


def cutoff_lewat(slot: Slot, sekarang: datetime | None = None) -> bool:
    """K14: muatan yang lewat cutoff berhenti menerima kiriman, tapi statusnya
    TETAP DIBUKA sampai petugas menutupnya — penutupan menetapkan harga final,
    membuat lot, dan memesan armada, jadi tidak boleh terjadi diam-diam sebagai
    efek samping sebuah GET."""
    return _aware(slot.cutoff_at) <= (sekarang or sekarang_utc())


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


def _pastikan_volume_minimal(db: Session, volume_kg: int) -> None:
    """K13: kiriman terlalu kecil ditolak — satu kiriman receh bisa menggeser
    rencana armada seluruh muatan dan menaikkan harga semua peserta."""
    minimal = baca_konfigurasi(db, "volume_minimal_kg")
    if volume_kg < minimal:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Volume minimal satu kiriman {minimal} kg (kamu mengisi {volume_kg} kg).",
        )


def _pastikan_dalam_jangkauan(db: Session, tk: TitikKumpul, lat: float, lng: float) -> float:
    """K13: tujuan bebas, tapi tetap ada batas kewajaran. Mengembalikan jarak rute."""
    faktor_jalan = baca_konfigurasi(db, "faktor_jalan")
    maks = baca_konfigurasi(db, "jarak_maks_layanan_km")
    jarak_rute = _jarak_haversine_km(tk.lat, tk.lng, lat, lng) * faktor_jalan
    if jarak_rute > maks:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Tujuan terlalu jauh: {jarak_rute:.0f} km dari titik kumpul, "
            f"batas layanan {maks:.0f} km.",
        )
    return jarak_rute


def _tujuan_atau_buat(db: Session, lat: float, lng: float, alamat: str) -> Penerima:
    """K13: pakai ulang alamat tujuan yang sudah dikenal kalau jaraknya di bawah
    `radius_dedup_tujuan_km`; kalau tidak, catat alamat baru. Inilah yang membuat
    tujuan benar-benar bebas tanpa membanjiri buku alamat dengan duplikat."""
    dedup = baca_konfigurasi(db, "radius_dedup_tujuan_km")
    terdekat: Penerima | None = None
    jarak_min = float("inf")
    for p in db.query(Penerima).all():
        jarak = _jarak_haversine_km(lat, lng, p.lat, p.lng)
        if jarak < jarak_min:
            jarak_min = jarak
            terdekat = p
    if terdekat is not None and jarak_min <= dedup:
        return terdekat

    baru = Penerima(
        nama=alamat.strip()[:120],
        # Tipe tidak memengaruhi perhitungan apa pun — hanya label tampilan.
        # Tujuan bebas tidak punya klasifikasi, jadi dipakai nilai paling umum.
        tipe=TipePenerima.HOREKA,
        alamat=alamat.strip(),
        lat=lat,
        lng=lng,
        dibuat_otomatis=True,
    )
    db.add(baru)
    db.flush()
    return baru


# K14: `_pilih_petugas` DIHAPUS. K13 menugaskan driver otomatis saat muatan
# lahir, tanpa batas apa pun — satu petugas aktif menyerap SELURUH muatan di
# sistem dan tidak ada endpoint yang bisa mengubahnya. Sekarang muatan lahir
# tanpa driver dan menunggu diambil lewat `POST /api/slot/{id}/terima`
# (papan tugas), dengan batas satu muatan aktif per petugas.


def _jadwal_muatan(db: Session, tanggal_kirim: date, sekarang: datetime) -> datetime:
    """K13: cutoff ditentukan sistem dari konfigurasi — bukan input siapa pun,
    dan bukan angka yang ditanam di kode (CLAUDE.md aturan #1).

    K14: cutoff TIDAK PERNAH lahir di masa lalu. Jadwal normal H-1 jam 18 WIB
    sudah lewat kalau petani mengirim untuk besok pada malam hari, sehingga
    muatan baru langsung tampil kedaluwarsa dan hitung mundurnya nol. Muatan
    yang baru dibuka selalu diberi jeda minimal supaya petani lain sempat ikut.
    """
    jam_cutoff = baca_konfigurasi(db, "jam_cutoff_default")
    hari_sebelum = baca_konfigurasi(db, "hari_cutoff_sebelum_kirim")
    offset_wib = baca_konfigurasi(db, "offset_wib_jam")
    jeda_minimal = baca_konfigurasi(db, "jeda_minimal_cutoff_menit")
    tengah_malam = datetime.combine(tanggal_kirim - timedelta(days=hari_sebelum), time(0, 0))
    # Aritmetika timedelta supaya jam negatif (mis. cutoff dini hari WIB) tetap benar.
    jadwal = (tengah_malam + timedelta(hours=jam_cutoff - offset_wib)).replace(tzinfo=timezone.utc)
    return max(jadwal, sekarang + timedelta(minutes=jeda_minimal))


def _titik_penerima(db: Session, penerima_ids: list[UUID]) -> list[TujuanInput]:
    baris = {p.id: p for p in db.query(Penerima).filter(Penerima.id.in_(penerima_ids)).all()}
    return [
        TujuanInput(penerima_id=pid, lat=baris[pid].lat, lng=baris[pid].lng)
        for pid in penerima_ids
        if pid in baris
    ]


def _titik_jemput_slot(db: Session, slot: Slot, tambahan: TujuanInput | None = None) -> list[TujuanInput]:
    """K14: lokasi penjemputan tiap peserta muatan ini.

    Diambil dari `Kiriman.lat_asal/lng_asal`. Kiriman lama (dan kiriman yang
    petaninya tidak menaruh titik jemput) tidak punya koordinat asal — mereka
    dilewati, sehingga muatannya berperilaku persis seperti sebelum K14 alih-alih
    memaksakan koordinat karangan."""
    kiriman = db.query(Kiriman).filter(Kiriman.slot_id == slot.id).all()
    titik = [
        TujuanInput(penerima_id=k.partisipasi_id, lat=k.lat_asal, lng=k.lng_asal)
        for k in kiriman
        if k.partisipasi_id is not None and k.lat_asal is not None and k.lng_asal is not None
    ]
    if tambahan is not None:
        titik.append(tambahan)
    return titik


def _rute_dua_tahap(
    db: Session, tk: TitikKumpul, jemput: list[TujuanInput], antar: list[TujuanInput]
) -> mesin.RuteDuaTahap:
    faktor_jalan = baca_konfigurasi(db, "faktor_jalan")
    return mesin.urutkan_rute_dua_tahap((tk.lat, tk.lng), jemput, antar, faktor_jalan)


def _alamat_jemput(db: Session, slot: Slot) -> dict[UUID, str]:
    """Alamat penjemputan per partisipasi — untuk ditampilkan ke petugas."""
    return {
        k.partisipasi_id: (k.alamat_asal or "Alamat penjemputan belum diisi")
        for k in db.query(Kiriman).filter(Kiriman.slot_id == slot.id).all()
        if k.partisipasi_id is not None
    }


def _tulis_rute(
    db: Session,
    tk: TitikKumpul,
    slot: Slot,
    penerima_ids: list[UUID],
    jemput_tambahan: TujuanInput | None = None,
) -> None:
    """Tulis ulang SELURUH rute muatan — dua tahap, jemput lalu antar (K14).

    `slot.jarak_km` menjadi total kedua tahap, jadi harga otomatis ikut jujur:
    leg penjemputan dulu tidak pernah masuk hitungan sama sekali."""
    antar = _titik_penerima(db, penerima_ids)
    jemput = _titik_jemput_slot(db, slot, jemput_tambahan)
    rute = _rute_dua_tahap(db, tk, jemput, antar)

    db.query(SlotTujuan).filter_by(slot_id=slot.id).delete(synchronize_session=False)
    db.query(SlotJemput).filter_by(slot_id=slot.id).delete(synchronize_session=False)
    db.flush()

    alamat = _alamat_jemput(db, slot)
    koordinat = {t.penerima_id: t for t in jemput}
    for j in rute.jemput:
        titik = koordinat[j.penerima_id]
        db.add(
            SlotJemput(
                slot_id=slot.id,
                partisipasi_id=j.penerima_id,
                urutan=j.urutan,
                lat=titik.lat,
                lng=titik.lng,
                alamat=alamat.get(j.penerima_id, "Alamat penjemputan belum diisi"),
                jarak_segmen_km=Decimal(str(round(j.jarak_segmen_km, 2))),
            )
        )
    for t in rute.antar:
        db.add(
            SlotTujuan(
                slot_id=slot.id,
                penerima_id=t.penerima_id,
                urutan=t.urutan,
                jarak_segmen_km=Decimal(str(round(t.jarak_segmen_km, 2))),
            )
        )
    slot.jarak_km = Decimal(str(round(rute.jarak_total_km, 2)))
    db.flush()
    db.expire(slot, ["tujuan", "jemput"])


def _slot_kandidat(
    db: Session,
    tk_id: UUID,
    lat_tujuan: float,
    lng_tujuan: float,
    tanggal_siap: date,
    jendela_hari: int,
    radius_koridor_km: float,
    sekarang: datetime,
) -> list[Slot]:
    """Slot DIBUKA di titik kumpul yang sama, tanggal dalam jendela, dan salah
    satu tujuan rutenya berada dalam radius koridor dari tujuan kiriman —
    urut pendaftaran (yang daftar duluan diisi duluan, §3.2).

    Pencocokan mengukur jarak ke TITIK TUJUAN slot (koridor), bukan kesetaraan
    penerima — dua petani dengan tujuan berbeda tapi berdekatan masuk muatan
    yang sama (§8.2: Wati 8 km dari tujuan Asep).

    K14: muatan yang sudah lewat cutoff tidak lagi menjadi kandidat. Sebelumnya
    cutoff hanya hiasan layar — slot kedaluwarsa tetap menyerap kiriman baru."""
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
        if cutoff_lewat(s, sekarang):
            continue
        jarak_min = float("inf")
        for t in s.tujuan:
            p = db.get(Penerima, t.penerima_id)
            if p is not None:
                jarak_min = min(jarak_min, _jarak_haversine_km(lat_tujuan, lng_tujuan, p.lat, p.lng))
        if jarak_min <= radius_koridor_km:
            cocok.append(s)
    return cocok


def _harga_berjalan_slot(db: Session, slot: Slot) -> int | None:
    if slot.volume_terkunci_kg <= 0:
        return None
    tiers, maks = baca_tiers_aktif(db), baca_konfigurasi(db, "maks_kendaraan")
    try:
        rencana = mesin.rencana_armada(slot.volume_terkunci_kg, float(slot.jarak_km), tiers, maks)
    except mesin.VolumeTerlaluBesar:
        return None
    return math.ceil(rencana.biaya_total / slot.volume_terkunci_kg)


@dataclass(frozen=True)
class HasilGabung:
    """Hasil simulasi "bagaimana kalau kiriman ini bergabung ke muatan itu"."""

    jarak_km: float
    harga_per_kg: int


def _cek_gabung(
    db: Session,
    tk: TitikKumpul,
    calon: Slot,
    tujuan: TujuanInput,
    volume_kg: int,
    tiers,
    maks: int,
    jemput_baru: TujuanInput | None = None,
) -> HasilGabung | None:
    """K13: boleh bergabung HANYA kalau tidak merugikan peserta yang sudah ada.
    Mengembalikan rute & harga sesudah bergabung, atau None kalau tidak boleh.

    Dua hal diperiksa dengan rute & volume SESUDAH bergabung:
    1. armada masih sanggup;
    2. harga berjalan grup tidak NAIK. Mesin armada memilih biaya total
       terendah, tapi biaya itu fungsi tangga — melewati batas kapasitas tier
       bisa menaikkan harga per kg semua orang (mis. 800 → 801 kg). Kalau itu
       terjadi, kiriman ini lebih baik membuka muatan sendiri.

    K14: tujuan calon masuk sebagai KOORDINAT, bukan id. Versi lama menerima
    objek penerima dan menyaringnya lewat query id — pada pratinjau id itu
    `None`, sehingga tujuan baru diam-diam hilang dari simulasi dan jarak
    (juga harga) yang dikembalikan adalah jarak muatan LAMA.
    """
    sudah_ada = [t.penerima_id for t in calon.tujuan]
    titik = _titik_penerima(db, sudah_ada)
    if tujuan.penerima_id not in sudah_ada:
        titik = titik + [tujuan]

    # K14: simulasi memakai rute LENGKAP — termasuk belokan menjemput panen
    # petani ini. Kalau tidak, harga yang dijanjikan lebih murah daripada rute
    # yang benar-benar ditempuh.
    jemput = _titik_jemput_slot(db, calon, jemput_baru)
    jarak_baru = _rute_dua_tahap(db, tk, jemput, titik).jarak_total_km
    volume_baru = calon.volume_terkunci_kg + volume_kg

    try:
        rencana_baru = mesin.rencana_armada(volume_baru, jarak_baru, tiers, maks)
    except (mesin.VolumeKosong, mesin.VolumeTerlaluBesar):
        return None

    harga_baru = math.ceil(rencana_baru.biaya_total / volume_baru)
    if calon.volume_terkunci_kg <= 0:
        return HasilGabung(jarak_km=jarak_baru, harga_per_kg=harga_baru)

    harga_lama = mesin.harga_berjalan_per_kg(calon.volume_terkunci_kg, float(calon.jarak_km), tiers, maks)
    if harga_baru > harga_lama:
        return None
    return HasilGabung(jarak_km=jarak_baru, harga_per_kg=harga_baru)


def _tujuan_simulasi(lat: float, lng: float) -> TujuanInput:
    """Tujuan sementara untuk pratinjau — id acak yang tidak pernah cocok dengan
    tujuan mana pun, jadi ia selalu dihitung sebagai perhentian tambahan."""
    return TujuanInput(penerima_id=uuid4(), lat=lat, lng=lng)


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
    minimal = baca_konfigurasi(db, "volume_minimal_kg")
    maks_km = baca_konfigurasi(db, "jarak_maks_layanan_km")
    faktor_jalan = baca_konfigurasi(db, "faktor_jalan")
    tiers, maks = baca_tiers_aktif(db), baca_konfigurasi(db, "maks_kendaraan")

    jarak_rute = _jarak_haversine_km(tk.lat, tk.lng, lat, lng) * faktor_jalan

    # Pratinjau tidak pernah melempar galat — ia memandu, bukan menghakimi.
    if volume_kg < minimal:
        return KirimanPratinjauResponse(
            slot_cocok_ada=False,
            jarak_ke_penerima_km=round(jarak_rute, 1),
            pesan=f"Volume minimal satu kiriman {minimal} kg.",
        )
    if jarak_rute > maks_km:
        return KirimanPratinjauResponse(
            slot_cocok_ada=False,
            jarak_ke_penerima_km=round(jarak_rute, 1),
            pesan=f"Tujuan terlalu jauh ({jarak_rute:.0f} km), batas layanan {maks_km:.0f} km.",
        )

    try:
        atap = mesin.harga_atap_per_kg(volume_kg, jarak_rute, tiers, maks)
    except (mesin.VolumeKosong, mesin.VolumeTerlaluBesar) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc))

    # K14: simulasi memakai kandidat PERTAMA yang lolos — persis urutan dan
    # syarat yang dipakai `buat_kiriman`, supaya angka di pratinjau adalah angka
    # yang benar-benar didapat petani.
    tujuan_semu = _tujuan_simulasi(lat, lng)
    kandidat = _slot_kandidat(db, tk.id, lat, lng, tanggal_siap, jendela, radius, sekarang_utc())
    hasil: HasilGabung | None = None
    for s in kandidat:
        hasil = _cek_gabung(db, tk, s, tujuan_semu, volume_kg, tiers, maks)
        if hasil is not None:
            break

    if hasil is not None:
        potensi = hasil.harga_per_kg
        cocok = True
        pesan = "Sudah ada muatan ke arah yang sama — kamu langsung ikut, ongkos dibagi bersama."
    else:
        # Proyeksi "kalau ada petani lain seukuran kamu ke arah yang sama" (§3.4).
        potensi = mesin.harga_berjalan_per_kg(volume_kg * 4, jarak_rute, tiers, maks)
        cocok = False
        pesan = "Belum ada muatan ke arah ini — muatan baru dibuka atas namamu."

    return KirimanPratinjauResponse(
        harga_atap_per_kg=atap,
        harga_potensial_per_kg=potensi,
        slot_cocok_ada=cocok,
        jarak_ke_penerima_km=round(jarak_rute, 1),
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

    _pastikan_volume_minimal(db, body.volume_kg)
    jarak_tujuan = _pastikan_dalam_jangkauan(db, tk, body.lat_tujuan, body.lng_tujuan)

    radius = baca_konfigurasi(db, "radius_koridor_km")
    jendela = baca_konfigurasi(db, "jendela_hari")
    tiers, maks = baca_tiers_aktif(db), baca_konfigurasi(db, "maks_kendaraan")

    penerima = _tujuan_atau_buat(db, body.lat_tujuan, body.lng_tujuan, body.alamat_tujuan)

    sekarang = sekarang_utc()
    tujuan = TujuanInput(penerima_id=penerima.id, lat=penerima.lat, lng=penerima.lng)
    kandidat = _slot_kandidat(
        db, tk.id, body.lat_tujuan, body.lng_tujuan, body.tanggal_siap, jendela, radius, sekarang
    )
    slot: Slot | None = None
    baru_dibuat = False

    # K14: titik penjemputan petani ini ikut disimulasikan — belokan menjemput
    # panennya menambah rute, jadi harus masuk hitungan sebelum diputuskan boleh
    # bergabung atau tidak. Placeholder id sementara; id sungguhan (partisipasi)
    # baru ada setelah barisnya dibuat di bawah.
    jemput_calon: TujuanInput | None = None
    if body.lat_asal is not None and body.lng_asal is not None:
        jemput_calon = TujuanInput(penerima_id=uuid4(), lat=body.lat_asal, lng=body.lng_asal)

    for calon in kandidat:
        if _cek_gabung(db, tk, calon, tujuan, body.volume_kg, tiers, maks, jemput_calon) is not None:
            slot = calon
            break

    if slot is None:
        tanggal_kirim = body.tanggal_siap
        nn = db.query(Slot).filter_by(titik_kumpul_id=tk.id, tanggal_kirim=tanggal_kirim).count() + 1
        slot = Slot(
            kode=f"SM-{tanggal_kirim:%Y%m%d}-{tk.kode}-{nn:02d}",
            titik_kumpul_id=tk.id,
            # K14: lahir TANPA driver — menunggu diambil dari papan tugas.
            petugas_id=None,
            tanggal_kirim=tanggal_kirim,
            cutoff_at=_jadwal_muatan(db, tanggal_kirim, sekarang),
            status=StatusSlot.DIBUKA,
            jarak_km=Decimal(str(round(jarak_tujuan, 2))),
            volume_terkunci_kg=0,
            selisih_jaminan_atap=0,
        )
        db.add(slot)
        db.flush()
        baru_dibuat = True

    partisipasi = Partisipasi(
        slot_id=slot.id,
        petani_id=pengguna.id,
        komoditas_id=body.komoditas_id,
        volume_kg=body.volume_kg,
        # Diisi ulang di bawah dari rute FINAL; kolomnya NOT NULL jadi perlu
        # nilai sementara yang jelas-jelas tidak dipakai.
        harga_atap_per_kg=0,
        kembalian_rp=0,
        status=StatusPartisipasi.TERDAFTAR,
    )
    db.add(partisipasi)
    slot.volume_terkunci_kg += body.volume_kg
    db.flush()

    rincian_tujuan = body.rincian_tujuan
    rincian_asal = body.rincian_asal
    kiriman = Kiriman(
        petani_id=pengguna.id,
        komoditas_id=body.komoditas_id,
        volume_kg=body.volume_kg,
        tanggal_siap=body.tanggal_siap,
        lat_tujuan=body.lat_tujuan,
        lng_tujuan=body.lng_tujuan,
        alamat_tujuan=body.alamat_tujuan,
        nama_penerima=rincian_tujuan.nama if rincian_tujuan else None,
        telepon_penerima=rincian_tujuan.telepon if rincian_tujuan else None,
        jalan_tujuan=rincian_tujuan.jalan if rincian_tujuan else None,
        rt_rw_tujuan=rincian_tujuan.rt_rw if rincian_tujuan else None,
        desa_tujuan=rincian_tujuan.desa if rincian_tujuan else None,
        kecamatan_tujuan=rincian_tujuan.kecamatan if rincian_tujuan else None,
        kabupaten_tujuan=rincian_tujuan.kabupaten if rincian_tujuan else None,
        provinsi_tujuan=rincian_tujuan.provinsi if rincian_tujuan else None,
        kode_pos_tujuan=rincian_tujuan.kode_pos if rincian_tujuan else None,
        patokan_tujuan=rincian_tujuan.patokan if rincian_tujuan else None,
        lat_asal=body.lat_asal,
        lng_asal=body.lng_asal,
        alamat_asal=rincian_asal.alamat if rincian_asal else None,
        telepon_pengirim=rincian_asal.telepon if rincian_asal else None,
        jalan_asal=rincian_asal.jalan if rincian_asal else None,
        rt_rw_asal=rincian_asal.rt_rw if rincian_asal else None,
        desa_asal=rincian_asal.desa if rincian_asal else None,
        kecamatan_asal=rincian_asal.kecamatan if rincian_asal else None,
        kabupaten_asal=rincian_asal.kabupaten if rincian_asal else None,
        provinsi_asal=rincian_asal.provinsi if rincian_asal else None,
        kode_pos_asal=rincian_asal.kode_pos if rincian_asal else None,
        patokan_asal=rincian_asal.patokan if rincian_asal else None,
        penerima_id=penerima.id,
        slot_id=slot.id,
        partisipasi_id=partisipasi.id,
    )
    db.add(kiriman)
    db.flush()

    # K14: rute ditulis SETELAH kiriman ada, karena tahap jemput dibaca dari
    # koordinat asal kiriman. Dijalankan untuk muatan baru maupun yang bertambah
    # peserta — leg jemput selalu berubah begitu ada satu petani lagi.
    penerima_ids = [t.penerima_id for t in slot.tujuan]
    if penerima.id not in penerima_ids:
        penerima_ids = penerima_ids + [penerima.id]
    _tulis_rute(db, tk, slot, penerima_ids)

    jarak_slot = float(slot.jarak_km)
    try:
        atap = mesin.harga_atap_per_kg(body.volume_kg, jarak_slot, tiers, maks)
    except (mesin.VolumeKosong, mesin.VolumeTerlaluBesar) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc))
    partisipasi.harga_atap_per_kg = atap

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
