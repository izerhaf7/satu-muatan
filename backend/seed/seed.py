"""Seed: konfigurasi + tier_kendaraan (Fase 0, spec §4.2 + KEPUTUSAN.md K6),
plus data induk (titik_kumpul, penerima, komoditas, pengguna K9) untuk Fase 2,
plus 8 slot riwayat SELESAI (Fase 3, spec §11.1) supaya Dashboard Dampak &
Beranda punya grafik terisi saat demo.

IDEMPOTEN: upsert per kunci alami — aman dijalankan berulang (DoD §14).
Skenario demo (reset ke keadaan awal §11.2) ada di `seed/skenario_demo.py`.

Jalankan dari folder backend:  python seed/seed.py
"""

import pathlib
import sys
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session  # noqa: E402

from app.auth import hash_pin  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.domain.armada import TujuanInput, urutkan_tujuan_nearest_neighbor  # noqa: E402
from app.domain.atribusi import ambang_transit_menit, tentukan_atribusi  # noqa: E402
from app.domain.harga import PartisipasiHarga, harga_atap_per_kg, tetapkan_harga_final  # noqa: E402
from app.models import (  # noqa: E402
    Atribusi,
    KeputusanSerahTerima,
    Komoditas,
    Konfigurasi,
    TitikKumpul,
    Lot,
    Partisipasi,
    Penerima,
    Pengguna,
    Pengiriman,
    PeranPengguna,
    Permintaan,
    SerahTerima,
    Slot,
    SlotTujuan,
    StatusPartisipasi,
    StatusPermintaan,
    StatusSlot,
    StatusSumber,
    TierKendaraan,
    TipeKonfigurasi,
    TipePenerima,
)
from app.services.konfigurasi import baca_konfigurasi, baca_tiers_aktif  # noqa: E402

CATATAN_TARIF = (
    "Struktur tarif dasar + per km Deliveree, referensi Jabodetabek yang dipakai "
    "sebagai acuan nasional; wilayah Jawa non-Jabodetabek tercatat sedikit lebih "
    "rendah. Diakses Juli 2026."
)

# kode, nama, kapasitas_kg, tarif_dasar, tarif_per_km, urutan, status, catatan
TIER_SEED = [
    ("MOBIL", "Mobil Ekonomi", 150, 39_000, 2_900, 1, StatusSumber.TERVERIFIKASI, CATATAN_TARIF),
    ("VAN", "Van", 800, 92_000, 3_000, 2, StatusSumber.TERVERIFIKASI, CATATAN_TARIF),
    ("PICKUP", "Pickup Kecil", 600, 110_000, 3_500, 3, StatusSumber.TERVERIFIKASI, CATATAN_TARIF),
    ("BOX", "Box Truck Kecil", 800, 162_000, 2_667, 4, StatusSumber.TERVERIFIKASI, CATATAN_TARIF),
    ("ENGKEL", "CDD / Truk Engkel", 2_000, 279_000, 3_300, 5, StatusSumber.TERVERIFIKASI, CATATAN_TARIF),
    ("FUSO", "Truk Fuso", 4_000, 350_000, 3_800, 6, StatusSumber.ASUMSI, CATATAN_TARIF + " Nilai FUSO diinterpolasi."),
]

# kunci, nilai, tipe, label, satuan, status, catatan
KONFIGURASI_SEED = [
    ("faktor_jalan", "1.30", TipeKonfigurasi.FLOAT, "Faktor koreksi jarak lurus → jarak jalan", None,
     StatusSumber.ASUMSI, "Perkiraan tim untuk medan Jawa Barat; belum diverifikasi."),
    ("kecepatan_rata_kmh", "35", TipeKonfigurasi.INT, "Kecepatan rata-rata truk", "km/jam",
     StatusSumber.ASUMSI, "Perkiraan tim; belum diverifikasi."),
    ("faktor_toleransi_transit", "1.50", TipeKonfigurasi.FLOAT,
     "Toleransi waktu transit sebelum dianggap terlambat", None,
     StatusSumber.ASUMSI, "Perkiraan tim; belum diverifikasi."),
    ("faktor_emisi_kg_co2_per_km", "0.25", TipeKonfigurasi.FLOAT, "Emisi CO₂e per truk-km", "kg CO₂e/km",
     StatusSumber.ASUMSI, "Perkiraan tim dari rentang publikasi faktor emisi truk ringan; belum diverifikasi."),
    ("biaya_asisten_muat", "75000", TipeKonfigurasi.INT, "Biaya asisten tambahan per pemesanan", "Rp",
     StatusSumber.TERVERIFIKASI, "Tarif publik layanan asisten Deliveree, diakses Juli 2026."),
    ("pakai_asisten_muat", "false", TipeKonfigurasi.BOOL, "Aktifkan biaya asisten dalam perhitungan", None,
     StatusSumber.ASUMSI, None),
    ("margin_platform_persen", "0", TipeKonfigurasi.FLOAT, "Margin platform (0 untuk MVP)", "%",
     StatusSumber.ASUMSI, None),
    ("jam_cutoff_default", "18", TipeKonfigurasi.INT, "Jam cutoff default slot", "jam",
     StatusSumber.ASUMSI, None),
    # K6 — tanpa kunci ini kartu "susut dicegah" tidak pernah terisi
    ("jam_dihemat_per_kirim", "4.0", TipeKonfigurasi.FLOAT,
     "Jam tunggu yang dihemat vs kirim sendiri-sendiri", "jam",
     StatusSumber.ASUMSI, "Perkiraan tim; belum diverifikasi."),
    # K6 — §5.2 meng-hardcode 4; dipindah ke konfigurasi sesuai aturan §4.1
    ("maks_kendaraan", "4", TipeKonfigurasi.INT, "Jumlah kendaraan maksimum per slot", "unit",
     StatusSumber.ASUMSI, None),
    # v2 §3.3 — pencocokan otomatis (C0)
    ("radius_koridor_km", "15", TipeKonfigurasi.FLOAT, "Radius pengelompokan tujuan", "km",
     StatusSumber.ASUMSI, "Perkiraan tim untuk koridor kecamatan; belum diverifikasi."),
    ("jendela_hari", "1", TipeKonfigurasi.INT, "Toleransi selisih tanggal kirim", "hari",
     StatusSumber.ASUMSI, "Perkiraan tim; belum diverifikasi."),
    # v2 §5.2 — generator telemetri dummy (C2)
    ("suhu_dasar_c", "26", TipeKonfigurasi.FLOAT, "Suhu dasar kurva harian telemetri", "°C",
     StatusSumber.ASUMSI, "Perkiraan iklim Jawa Barat; belum diverifikasi."),
    ("amplitudo_suhu_c", "8", TipeKonfigurasi.FLOAT, "Amplitudo suhu kurva harian telemetri", "°C",
     StatusSumber.ASUMSI, "Perkiraan tim; belum diverifikasi."),
    ("interval_telemetri_menit", "10", TipeKonfigurasi.INT, "Interval sampel telemetri simulasi", "menit",
     StatusSumber.ASUMSI, None),
    # v2 §6.4 — atribusi 3-input (C3)
    ("ambang_grade_asal", "3", TipeKonfigurasi.INT, "Grade minimum agar barang boleh dimuat", None,
     StatusSumber.ASUMSI, "Perkiraan tim; belum diverifikasi."),
    ("ambang_paparan_persen", "50", TipeKonfigurasi.INT,
     "Batas sisa umur simpan dianggap paparan berlebih", "%",
     StatusSumber.ASUMSI, "Perkiraan tim; belum diverifikasi."),
]


def seed_tier(db: Session) -> int:
    baru = 0
    for kode, nama, kapasitas, dasar, per_km, urutan, status, catatan in TIER_SEED:
        tier = db.query(TierKendaraan).filter_by(kode=kode).one_or_none()
        if tier is None:
            tier = TierKendaraan(kode=kode)
            db.add(tier)
            baru += 1
        tier.nama = nama
        tier.kapasitas_kg = kapasitas
        tier.tarif_dasar = dasar
        tier.tarif_per_km = per_km
        tier.urutan = urutan
        tier.aktif = True
        tier.status_sumber = status
        tier.catatan_sumber = catatan
    return baru


def seed_konfigurasi(db: Session) -> int:
    baru = 0
    for kunci, nilai, tipe, label, satuan, status, catatan in KONFIGURASI_SEED:
        konf = db.get(Konfigurasi, kunci)
        if konf is None:
            konf = Konfigurasi(kunci=kunci, nilai=nilai)
            db.add(konf)
            baru += 1
        # nilai TIDAK ditimpa kalau baris sudah ada — perubahan lewat Panel Asumsi
        # harus selamat dari seed ulang; metadata (label dll.) selalu disegarkan.
        konf.tipe = tipe
        konf.label = label
        konf.satuan = satuan
        konf.status_sumber = status
        konf.catatan_sumber = catatan
    return baru


# ---------------------------------------------------------------------------
# Data induk (spec §11.1 + KEPUTUSAN.md K9) — koordinat gudang ASUMSI (perkiraan)

CATATAN_KOMODITAS = (
    "Harga acuan perkiraan tim; WAJIB diganti data PIHPS sebelum final (spec §11.1). "
    "Parameter Q10 & umur simpan: literatur umum postharvest — Q10 organ penyimpanan "
    "rendah, sayur daun tinggi (spec v2 §4.1, status ASUMSI)."
)

# nama, harga_acuan, umur_simpan_jam (pada suhu acuan), laju_susut_per_jam, q10, suhu_acuan_c
KOMODITAS_SEED = [
    ("Sawi hijau", 4_000, 36, Decimal("0.00830"), Decimal("3.5"), Decimal("25")),  # utama demo (§8.1)
    ("Kangkung", 3_500, 36, Decimal("0.00830"), Decimal("3.5"), Decimal("25")),
    ("Tomat", 5_000, 72, Decimal("0.00520"), Decimal("2.5"), Decimal("25")),
    ("Kubis", 3_000, 96, Decimal("0.00250"), Decimal("2.0"), Decimal("25")),
    ("Wortel", 6_000, 240, Decimal("0.00180"), Decimal("1.5"), Decimal("25")),
]

# nama, lat, lng
PENERIMA_SEED = [
    ("SPPG Cibiru 3", -6.9269, 107.7189),
    ("SPPG Ujungberung 1", -6.9147, 107.7000),
    ("SPPG Panyileukan 2", -6.9333, 107.6989),
]

# K9 — akun kanonik. (nama, no_hp, peran)
PENGGUNA_SEED = [
    ("Bu Nia", "081200000001", PeranPengguna.PETUGAS),
    ("Asep", "081200000011", PeranPengguna.PETANI),
    ("Wati", "081200000012", PeranPengguna.PETANI),
    ("Dedi", "081200000013", PeranPengguna.PETANI),
    ("Ijah", "081200000014", PeranPengguna.PETANI),
    ("Ujang", "081200000015", PeranPengguna.PETANI),
    ("Euis", "081200000016", PeranPengguna.PETANI),
    ("Bu Rina", "081200000021", PeranPengguna.PENERIMA),
]

PIN_DEMO = "123456"


# ---------------------------------------------------------------------------
# Riwayat (spec §11.1): 8 slot SELESAI tersebar ~60 hari ke belakang (anchor
# penulisan 2026-07-27, spasi mingguan tetap) — Dashboard Dampak & Beranda
# butuh grafik yang tidak kosong saat demo. Tanggal FIXED (bukan "hari ini − N"
# yang dihitung ulang tiap run) supaya kode slot deterministik selamanya, bukan
# cuma dalam sesi yang sama — syarat idempoten dijalankan dua kali (DoD §14)
# juga harus tahan dijalankan ulang di hari yang berbeda.
#
# tanggal, nama_komoditas, [nama_penerima tujuan...], [(nama_petani, volume_kg)...]
# Volume & jarak TIDAK PERNAH dihitung manual — seed_riwayat() memanggil
# app.domain.armada/harga/atribusi dengan koefisien dari tabel konfigurasi
# saat seed dijalankan (aturan keras CLAUDE.md #1).
RIWAYAT_SEED: list[tuple[date, str, list[str], list[tuple[str, int]]]] = [
    (date(2026, 5, 28), "Kubis", ["SPPG Cibiru 3"],
     [("Asep", 500), ("Wati", 400), ("Dedi", 300)]),
    (date(2026, 6, 4), "Tomat", ["SPPG Ujungberung 1", "SPPG Panyileukan 2"],
     [("Ijah", 350), ("Ujang", 350)]),
    (date(2026, 6, 11), "Sawi hijau", ["SPPG Cibiru 3", "SPPG Ujungberung 1", "SPPG Panyileukan 2"],
     [("Asep", 400), ("Wati", 380), ("Dedi", 350), ("Ijah", 340), ("Euis", 330)]),
    (date(2026, 6, 18), "Wortel", ["SPPG Panyileukan 2"],
     [("Wati", 320), ("Ujang", 280)]),
    (date(2026, 6, 25), "Kubis", ["SPPG Cibiru 3", "SPPG Panyileukan 2"],
     [("Dedi", 420), ("Ijah", 400), ("Euis", 380), ("Asep", 300)]),
    (date(2026, 7, 2), "Tomat", ["SPPG Ujungberung 1"],
     [("Wati", 260), ("Euis", 240), ("Ujang", 200)]),
    (date(2026, 7, 9), "Sawi hijau", ["SPPG Cibiru 3", "SPPG Ujungberung 1", "SPPG Panyileukan 2"],
     [("Asep", 450), ("Dedi", 430), ("Ijah", 420), ("Ujang", 400), ("Euis", 300)]),
    (date(2026, 7, 16), "Wortel", ["SPPG Cibiru 3"],
     [("Wati", 300), ("Asep", 200)]),
]  # fmt: skip

# NN selalu "01" — satu slot per tanggal riwayat (tidak ada slot kedua di hari sama).
RIWAYAT_SLOT_KODE = [f"SM-{tanggal:%Y%m%d}-CKJ-01" for tanggal, *_ in RIWAYAT_SEED]


def seed_induk(db: Session) -> int:
    baru = 0

    titik_kumpul = db.query(TitikKumpul).filter_by(kode="CKJ").one_or_none()
    if titik_kumpul is None:
        titik_kumpul = TitikKumpul(kode="CKJ")
        db.add(titik_kumpul)
        baru += 1
    titik_kumpul.nama = "Koperasi Desa Mekarjaya"
    titik_kumpul.desa = "Mekarjaya"
    titik_kumpul.kecamatan = "Cikajang"
    titik_kumpul.kabupaten = "Garut"
    titik_kumpul.alamat = "Jl. Raya Cikajang No. 12, Desa Mekarjaya"
    titik_kumpul.lat = -7.3661  # ASUMSI — perkiraan lokasi gudang (spec §11.1)
    titik_kumpul.lng = 107.7961
    db.flush()

    penerima_pertama = None
    for nama, lat, lng in PENERIMA_SEED:
        p = db.query(Penerima).filter_by(nama=nama).one_or_none()
        if p is None:
            p = Penerima(nama=nama)
            db.add(p)
            baru += 1
        p.tipe = TipePenerima.SPPG
        p.alamat = f"{nama}, Kota Bandung"
        p.lat = lat
        p.lng = lng
        db.flush()
        if penerima_pertama is None:
            penerima_pertama = p  # SPPG Cibiru 3 — dapur Bu Rina (K9)

    for nama, harga, umur, laju, q10, suhu_acuan in KOMODITAS_SEED:
        k = db.query(Komoditas).filter_by(nama=nama).one_or_none()
        if k is None:
            k = Komoditas(nama=nama)
            db.add(k)
            baru += 1
        k.satuan = "kg"
        k.harga_acuan_per_kg = harga
        k.umur_simpan_jam = umur
        k.laju_susut_per_jam = laju
        k.q10 = q10
        k.suhu_acuan_c = suhu_acuan
        k.status_sumber = StatusSumber.ASUMSI
        k.catatan_sumber = CATATAN_KOMODITAS

    for nama, no_hp, peran in PENGGUNA_SEED:
        u = db.query(Pengguna).filter_by(no_hp=no_hp).one_or_none()
        if u is None:
            # pin_hash hanya di-set saat baris dibuat — seed ulang tidak
            # mengganti PIN (dan tidak membayar biaya bcrypt berulang).
            u = Pengguna(no_hp=no_hp, pin_hash=hash_pin(PIN_DEMO))
            db.add(u)
            baru += 1
        u.nama = nama
        u.peran = peran
        u.aktif = True
        u.titik_kumpul_id = titik_kumpul.id if peran in (PeranPengguna.PETUGAS, PeranPengguna.PETANI) else None
        u.penerima_id = penerima_pertama.id if peran is PeranPengguna.PENERIMA else None

    return baru


def seed_riwayat(db: Session) -> int:
    """8 slot SELESAI historis (spec §11.1) — IDEMPOTEN: kalau `kode` sudah ada,
    slot itu (dan seluruh anaknya) dilewati apa adanya, fakta historis tidak
    pernah ditulis ulang. Panggil setelah `seed_induk`/`seed_tier`/`seed_konfigurasi`.

    Jarak, harga atap/final/kembalian, ambang transit, dan atribusi SELALU dihitung
    lewat `app.domain.armada/harga/atribusi` dengan koefisien dibaca dari tabel
    `konfigurasi`/`tier_kendaraan` saat fungsi ini dijalankan — tidak ada angka
    bisnis hardcoded di sini (CLAUDE.md aturan #1).
    """
    titik_kumpul = db.query(TitikKumpul).filter_by(kode="CKJ").one_or_none()
    if titik_kumpul is None:
        raise RuntimeError("seed_riwayat() butuh titik_kumpul CKJ — jalankan seed_induk() dulu")

    penerima_by_nama = {p.nama: p for p in db.query(Penerima).all()}
    komoditas_by_nama = {k.nama: k for k in db.query(Komoditas).all()}
    petani_by_nama = {u.nama: u for u in db.query(Pengguna).filter_by(peran=PeranPengguna.PETANI).all()}
    tier_row_by_kode = {t.kode: t for t in db.query(TierKendaraan).all()}

    tiers = baca_tiers_aktif(db)
    maks_kendaraan = baca_konfigurasi(db, "maks_kendaraan")
    faktor_jalan = baca_konfigurasi(db, "faktor_jalan")
    kecepatan = baca_konfigurasi(db, "kecepatan_rata_kmh")
    toleransi = baca_konfigurasi(db, "faktor_toleransi_transit")
    ambang_grade = baca_konfigurasi(db, "ambang_grade_asal")
    ambang_paparan = baca_konfigurasi(db, "ambang_paparan_persen")

    lot_idx = 0  # counter GLOBAL lintas slot — sumber variasi cacat/transit deterministik (bukan random)
    slot_baru = 0

    for tanggal, nama_komoditas, nama_tujuan_list, petani_volume in RIWAYAT_SEED:
        kode_slot = f"SM-{tanggal:%Y%m%d}-CKJ-01"
        if db.query(Slot).filter_by(kode=kode_slot).one_or_none() is not None:
            lot_idx += len(petani_volume)  # majukan counter walau di-skip — pola tetap konsisten
            continue

        komoditas = komoditas_by_nama[nama_komoditas]
        tujuan_penerima = [penerima_by_nama[n] for n in nama_tujuan_list]

        tujuan_input = [TujuanInput(penerima_id=p.id, lat=p.lat, lng=p.lng) for p in tujuan_penerima]
        urutan = urutkan_tujuan_nearest_neighbor((titik_kumpul.lat, titik_kumpul.lng), tujuan_input, faktor_jalan)
        jarak_total = sum(t.jarak_segmen_km for t in urutan)

        cutoff_at = datetime.combine(tanggal, time(11, 0), tzinfo=timezone.utc)  # 18:00 WIB (jam_cutoff_default)

        volume_total = sum(v for _, v in petani_volume)
        slot = Slot(
            kode=kode_slot,
            titik_kumpul_id=titik_kumpul.id,
            tanggal_kirim=tanggal,
            cutoff_at=cutoff_at,
            status=StatusSlot.SELESAI,
            jarak_km=Decimal(str(round(jarak_total, 2))),
            volume_terkunci_kg=volume_total,
            selisih_jaminan_atap=0,
            dibuat_pada=cutoff_at - timedelta(days=1),
        )
        db.add(slot)
        db.flush()  # butuh slot.id untuk baris anak

        for t in urutan:
            db.add(
                SlotTujuan(
                    slot_id=slot.id,
                    penerima_id=t.penerima_id,
                    urutan=t.urutan,
                    jarak_segmen_km=Decimal(str(round(t.jarak_segmen_km, 2))),
                )
            )

        partisipasi_rows: list[Partisipasi] = []
        partisipasi_harga_input: list[PartisipasiHarga] = []
        for nama_petani, volume in petani_volume:
            petani = petani_by_nama[nama_petani]
            atap = harga_atap_per_kg(volume, jarak_total, tiers, maks_kendaraan)
            pid = uuid.uuid4()
            partisipasi_harga_input.append(PartisipasiHarga(id=pid, volume_kg=volume, harga_atap_per_kg=atap))
            p = Partisipasi(
                id=pid,
                slot_id=slot.id,
                petani_id=petani.id,
                komoditas_id=komoditas.id,
                volume_kg=volume,
                harga_atap_per_kg=atap,
                status=StatusPartisipasi.SELESAI,
                bergabung_pada=cutoff_at - timedelta(hours=6),
            )
            db.add(p)
            partisipasi_rows.append(p)
        db.flush()  # Lot di bawah mereferensikan partisipasi_id lewat FK — tanpa relationship ORM,
        # SQLAlchemy tidak otomatis mengurutkan insert lintas tabel, jadi di-flush eksplisit dulu.

        hasil = tetapkan_harga_final(partisipasi_harga_input, jarak_total, tiers, maks_kendaraan)
        for p in partisipasi_rows:
            h_i = min(hasil.harga_final_per_kg, p.harga_atap_per_kg)
            p.harga_final_per_kg = h_i
            p.kembalian_rp = hasil.kembalian[p.id]

        tier_dominan = max(hasil.rencana.tier, key=lambda t: t.kapasitas_kg)
        slot.biaya_total = hasil.biaya_total
        slot.harga_final_per_kg = hasil.harga_final_per_kg
        slot.selisih_jaminan_atap = hasil.subsidi_koperasi
        slot.tier_terpilih_id = tier_row_by_kode[tier_dominan.kode].id
        slot.jumlah_kendaraan = len(hasil.rencana.tier)
        slot.rencana_json = {
            "tier": [{"kode": t.kode, "kapasitas_kg": t.kapasitas_kg} for t in hasil.rencana.tier],
            "biaya_total": hasil.rencana.biaya_total,
            "kapasitas_total_kg": hasil.rencana.kapasitas_total_kg,
            "tier_ringkas": "+".join(t.kode for t in hasil.rencana.tier),
        }

        ambang_menit = ambang_transit_menit(jarak_total, kecepatan, toleransi)

        # Alokasi lot -> tujuan: round-robin antar penerima yang dituju slot ini.
        lots_info: list[tuple[Lot, Partisipasi, Penerima, int, int]] = []
        waktu_muat_list = []
        for i, p in enumerate(partisipasi_rows):
            penerima_tujuan = tujuan_penerima[i % len(tujuan_penerima)]
            # ~1 dari 6 lot bermutu rendah sejak muat (grade 2 < ambang_grade_asal 3)
            grade_asal = 2 if lot_idx % 6 == 5 else 5
            waktu_muat = cutoff_at + timedelta(hours=2, minutes=10 * i)
            berat_aktual = max(1, p.volume_kg - (lot_idx % 7))  # variasi kecil vs volume komitmen (K3: bukti mutu)
            lot = Lot(
                id=uuid.uuid4(),  # di-set eksplisit (bukan default kolom) — SerahTerima di bawah butuh lot.id
                # sebelum flush, sama seperti pola id=pid pada Partisipasi di atas.
                partisipasi_id=p.id,
                kode_qr=f"LOT-{kode_slot}-{i + 1:02d}",
                penerima_id=penerima_tujuan.id,
                berat_aktual_kg=berat_aktual,
                waktu_muat=waktu_muat,
                grade_asal=grade_asal,
            )
            db.add(lot)
            waktu_muat_list.append(waktu_muat)
            lots_info.append((lot, p, penerima_tujuan, grade_asal, lot_idx))
            lot_idx += 1

        waktu_berangkat = max(waktu_muat_list) + timedelta(minutes=30)
        pengiriman = Pengiriman(
            slot_id=slot.id,
            vendor="MOCK",
            vendor_ref=f"MOCKV-HIST-{kode_slot}",
            status_vendor="TIBA",
            waktu_berangkat=waktu_berangkat,
            kuotasi_json={
                "tier_kode": tier_dominan.kode,
                "jarak_km": round(jarak_total, 2),
                "biaya_total": hasil.biaya_total,
            },
            dibuat_pada=cutoff_at,
        )
        db.add(pengiriman)

        penerima_volume_terkirim: dict[uuid.UUID, int] = {}
        waktu_bongkar_list = []
        for lot, p, penerima_tujuan, grade_asal, idx in lots_info:
            if grade_asal < 3:
                durasi = max(5, int(ambang_menit * 0.6))  # grade asal rendah menang di atribusi
                grade_tiba, sisa = 2, 75
            elif idx % 4 == 2:
                durasi = ambang_menit + 20  # LOGISTIK — transit melewati ambang
                grade_tiba, sisa = 3, 60
            else:
                durasi = max(5, ambang_menit - 25)  # TIDAK_TERBUKTI — masih di dalam ambang
                grade_tiba, sisa = 3, 71

            waktu_bongkar = waktu_berangkat + timedelta(minutes=durasi)
            waktu_bongkar_list.append(waktu_bongkar)

            atribusi_str = tentukan_atribusi(grade_asal, grade_tiba, durasi, ambang_menit, sisa, ambang_grade, ambang_paparan)
            if atribusi_str == Atribusi.PETANI.value:
                if idx % 12 == 11:
                    keputusan, persen, alasan = (
                        KeputusanSerahTerima.TOLAK,
                        0,
                        "Cacat terlihat sejak muat — kualitas tidak layak terima, lot ditolak seluruhnya.",
                    )
                else:
                    keputusan, persen, alasan = (
                        KeputusanSerahTerima.POTONG,
                        20,
                        "Cacat terlihat sejak muat — potongan 20% sesuai kesepakatan mutu.",
                    )
            elif atribusi_str == Atribusi.LOGISTIK.value:
                if idx % 8 == 6:
                    keputusan, persen, alasan = (
                        KeputusanSerahTerima.POTONG,
                        10,
                        "Transit melebihi ambang waktu rute — potongan 10% akibat penyusutan selama perjalanan.",
                    )
                else:
                    keputusan, persen, alasan = KeputusanSerahTerima.TERIMA, 0, None
            else:
                if idx % 10 == 9:
                    keputusan, persen, alasan = (
                        KeputusanSerahTerima.POTONG,
                        5,
                        "Variasi mutu alami saat bongkar — potongan kecil disepakati di tempat.",
                    )
                else:
                    keputusan, persen, alasan = KeputusanSerahTerima.TERIMA, 0, None

            db.add(
                SerahTerima(
                    lot_id=lot.id,
                    penerima_id=penerima_tujuan.id,
                    waktu_bongkar=waktu_bongkar,
                    keputusan=keputusan,
                    persen_potongan=persen,
                    alasan=alasan,
                    durasi_transit_menit=durasi,
                    ambang_transit_menit=ambang_menit,
                    atribusi=Atribusi(atribusi_str),
                    grade_tiba=grade_tiba,
                    sisa_umur_simpan_persen=sisa,
                )
            )
            penerima_volume_terkirim[penerima_tujuan.id] = (
                penerima_volume_terkirim.get(penerima_tujuan.id, 0) + p.volume_kg
            )

        pengiriman.waktu_tiba = max(waktu_bongkar_list)

        # Riwayat permintaan (K6) — tautkan ke tujuan pertama rute, terpenuhi penuh.
        tujuan_pertama = tujuan_penerima[0]
        volume_terpenuhi = penerima_volume_terkirim.get(tujuan_pertama.id, 0)
        if volume_terpenuhi > 0:
            db.add(
                Permintaan(
                    penerima_id=tujuan_pertama.id,
                    komoditas_id=komoditas.id,
                    volume_kg=volume_terpenuhi,
                    tanggal_dibutuhkan=tanggal,
                    status=StatusPermintaan.TERPENUHI,
                    slot_id=slot.id,
                    volume_terpenuhi_kg=volume_terpenuhi,
                    dibuat_pada=cutoff_at - timedelta(days=2),
                )
            )

        slot_baru += 1

    return slot_baru


def main() -> None:
    db = SessionLocal()
    try:
        tier_baru = seed_tier(db)
        konf_baru = seed_konfigurasi(db)
        induk_baru = seed_induk(db)
        db.commit()
        riwayat_baru = seed_riwayat(db)
        db.commit()
        print(
            f"Seed selesai: {tier_baru} tier baru, {konf_baru} konfigurasi baru, "
            f"{induk_baru} data induk baru, {riwayat_baru} slot riwayat baru (sisanya di-update/dilewati)."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
