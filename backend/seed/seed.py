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
from app.domain.mutu import hitung_indeks_mutu  # noqa: E402
from app.services.foto_contoh import FOTO_PLACEHOLDER_DEMO  # noqa: E402
try:  # noqa: E402 — dua cara pemanggilan yang sama-sama sah
    from seed.wilayah import seed_wilayah
except ModuleNotFoundError:
    # `python seed/seed.py` menaruh folder seed/ sendiri di sys.path[0],
    # sehingga nama `seed` menunjuk berkas ini, bukan foldernya.
    from wilayah import seed_wilayah  # type: ignore[no-redef]
from app.models import (  # noqa: E402
    Atribusi,
    KeputusanSerahTerima,
    Kiriman,
    Komoditas,
    Konfigurasi,
    TitikKumpul,
    Lot,
    Partisipasi,
    Penerima,
    Pengguna,
    Pengiriman,
    PeranPengguna,
    SerahTerima,
    Slot,
    SlotTujuan,
    StatusPartisipasi,
    StatusSlot,
    StatusSumber,
    Telemetri,
    TierKendaraan,
    TipeKonfigurasi,
    TipePenerima,
    TipeTitikKumpul,
)
from app.services.konfigurasi import baca_konfigurasi, baca_tiers_aktif  # noqa: E402
from app.services.telemetri import bangkitkan_telemetri  # noqa: E402

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
    # K13 — tujuan bebas, volume minimal, jadwal & driver ditentukan sistem
    ("volume_minimal_kg", "50", TipeKonfigurasi.INT, "Volume minimal satu kiriman", "kg",
     StatusSumber.ASUMSI, "Ambang tim supaya kiriman sangat kecil tidak menggeser harga seluruh muatan."),
    ("jarak_maks_layanan_km", "200", TipeKonfigurasi.FLOAT, "Jarak tujuan terjauh yang dilayani", "km",
     StatusSumber.ASUMSI, "Batas kewajaran tim untuk sekali jalan pulang-hari; belum diverifikasi."),
    ("radius_dedup_tujuan_km", "0.50", TipeKonfigurasi.FLOAT,
     "Dua titik tujuan sedekat ini dianggap alamat yang sama", "km",
     StatusSumber.ASUMSI, "Perkiraan tim; belum diverifikasi."),
    ("jam_berangkat_default", "6", TipeKonfigurasi.INT, "Jam berangkat muatan (ditentukan sistem)", "jam",
     StatusSumber.ASUMSI, None),
    ("hari_cutoff_sebelum_kirim", "1", TipeKonfigurasi.INT, "Cutoff ditutup berapa hari sebelum kirim", "hari",
     StatusSumber.ASUMSI, None),
    ("offset_wib_jam", "7", TipeKonfigurasi.INT, "Selisih WIB terhadap UTC", "jam",
     StatusSumber.TERVERIFIKASI, "WIB = UTC+7."),
    # K14 — indeks mutu yang dilihat penerima SEBELUM memutuskan
    ("bobot_mutu_umur_simpan", "0.7", TipeKonfigurasi.FLOAT,
     "Bobot sisa umur simpan dalam indeks mutu", None,
     StatusSumber.ASUMSI, "Umur simpan dianggap sinyal mutu terkuat; waktu tempuh pendukung."),
    ("bobot_mutu_transit", "0.3", TipeKonfigurasi.FLOAT,
     "Bobot ketepatan waktu tempuh dalam indeks mutu", None,
     StatusSumber.ASUMSI, "Perkiraan tim; belum diverifikasi."),
    ("ambang_tolak_persen", "50", TipeKonfigurasi.INT,
     "Penurunan mutu minimum agar barang boleh ditolak", "%",
     StatusSumber.ASUMSI, "Di bawah ini penerima wajib menerima — mencegah penolakan sepihak."),
    # K14 — papan tugas petugas
    ("maks_muatan_aktif_per_petugas", "1", TipeKonfigurasi.INT,
     "Muatan aktif maksimum yang boleh dibawa satu petugas", "muatan",
     StatusSumber.ASUMSI, "Satu sopir tidak bisa membawa dua truk sekaligus."),
    # K14 — cutoff tidak boleh lahir di masa lalu
    ("jeda_minimal_cutoff_menit", "120", TipeKonfigurasi.INT,
     "Jeda minimal antara muatan dibuka dan cutoff-nya", "menit",
     StatusSumber.ASUMSI, "Waktu minimum agar petani lain sempat ikut sebelum muatan dikunci."),
    ("langkah_geser_demo", "10", TipeKonfigurasi.INT,
     "Jumlah langkah posisi dari titik kumpul sampai tujuan (mode demo)", "langkah",
     StatusSumber.ASUMSI, "Hanya memengaruhi kehalusan animasi peta saat demo, bukan perhitungan bisnis."),
    ("rute_provider", "AUTO", TipeKonfigurasi.STRING,
     "Penyedia rute untuk perhitungan jarak/waktu (GOOGLE | HAVERSINE | AUTO)", None,
     StatusSumber.ASUMSI, "AUTO memilih penyedia terbaik yang tersedia; hanya memengaruhi perhitungan rute."),
    ("simulasi_percepatan_x", "60.0", TipeKonfigurasi.FLOAT,
     "Faktor percepatan waktu mode demo", "x",
     StatusSumber.ASUMSI, "Kompresi waktu simulasi saat demo; tidak menyentuh perhitungan bisnis."),
    ("radius_sampai_m", "5.0", TipeKonfigurasi.FLOAT,
     "Radius deteksi 'sudah sampai' tujuan", "m",
     StatusSumber.ASUMSI, "Jarak ke tujuan yang dianggap sudah tiba."),
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

# nama, lat, lng — nama netral v2 §8.1 (tanpa "SPPG"); enum TipePenerima tetap.
PENERIMA_SEED = [
    ("Dapur Katering Cibiru", -6.9269, 107.7189),
    ("Pasar Ujungberung", -6.9147, 107.7000),
    ("Rumah Makan Panyileukan", -6.9333, 107.6989),
]

# Nama v1 → nama v2 (§8.1) — baris lama di-rename in-place, bukan dibuat ulang,
# supaya riwayat yang sudah menempel tidak yatim. Kunci = nama lama apa adanya
# di data v1 (bukan copy produk, murni kebutuhan migrasi data).
PENERIMA_NAMA_LAMA = {
    "SPPG Cibiru 3": "Dapur Katering Cibiru",
    "SPPG Ujungberung 1": "Pasar Ujungberung",
    "SPPG Panyileukan 2": "Rumah Makan Panyileukan",
}

# K9 — akun kanonik v2 (§8.1). (nama, no_hp, peran)
# Asep = petani yang ditunjuk sebagai PETUGAS di titik kumpulnya sendiri (§2.3).
PENGGUNA_SEED = [
    ("Asep", "081200000011", PeranPengguna.PETUGAS),
    ("Bu Nia", "081200000001", PeranPengguna.PETANI),
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
    (date(2026, 5, 28), "Sawi hijau", ["Dapur Katering Cibiru"],
     [("Asep", 500), ("Wati", 400), ("Dedi", 300)]),
    (date(2026, 6, 4), "Tomat", ["Pasar Ujungberung", "Rumah Makan Panyileukan"],
     [("Ijah", 350), ("Ujang", 350)]),
    (date(2026, 6, 11), "Sawi hijau", ["Dapur Katering Cibiru", "Pasar Ujungberung", "Rumah Makan Panyileukan"],
     [("Asep", 400), ("Wati", 380), ("Dedi", 350), ("Ijah", 340), ("Euis", 330)]),
    (date(2026, 6, 18), "Wortel", ["Rumah Makan Panyileukan"],
     [("Wati", 320), ("Ujang", 280)]),
    (date(2026, 6, 25), "Kubis", ["Dapur Katering Cibiru", "Rumah Makan Panyileukan"],
     [("Dedi", 420), ("Ijah", 400), ("Euis", 380), ("Asep", 300)]),
    (date(2026, 7, 2), "Tomat", ["Pasar Ujungberung"],
     [("Wati", 260), ("Euis", 240), ("Ujang", 200)]),
    (date(2026, 7, 9), "Sawi hijau", ["Dapur Katering Cibiru", "Pasar Ujungberung", "Rumah Makan Panyileukan"],
     [("Asep", 450), ("Dedi", 430), ("Ijah", 420), ("Ujang", 400), ("Euis", 300)]),
    (date(2026, 7, 16), "Wortel", ["Dapur Katering Cibiru"],
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
    titik_kumpul.nama = "Titik Kumpul Pak Asep"
    titik_kumpul.tipe = TipeTitikKumpul.PETANI_UTAMA
    titik_kumpul.desa = "Mekarjaya"
    titik_kumpul.kecamatan = "Cikajang"
    titik_kumpul.kabupaten = "Garut"
    titik_kumpul.alamat = "Jl. Raya Cikajang No. 12, Desa Mekarjaya"
    titik_kumpul.lat = -7.3661  # ASUMSI — perkiraan lokasi titik kumpul (spec §11.1)
    titik_kumpul.lng = 107.7961
    db.flush()

    penerima_pertama = None
    for nama_lama, nama_baru in PENERIMA_NAMA_LAMA.items():
        lama = db.query(Penerima).filter_by(nama=nama_lama).one_or_none()
        if lama is None:
            continue
        # Kalau baris bernama baru SUDAH ada (mis. sempat ter-seed sebelum
        # migrasi nama jalan): alihkan seluruh dependensinya ke baris lama
        # (kanonik), lalu hapus duplikatnya — bukan membiarkan nama ganda.
        for d in db.query(Penerima).filter(Penerima.nama == nama_baru, Penerima.id != lama.id).all():
            for model, kolom in (
                (SlotTujuan, "penerima_id"),
                (Kiriman, "penerima_id"),
                (Pengguna, "penerima_id"),
                (Lot, "penerima_id"),
                (SerahTerima, "penerima_id"),
            ):
                db.query(model).filter_by(**{kolom: d.id}).update({kolom: lama.id}, synchronize_session=False)
            db.delete(d)
        lama.nama = nama_baru
        db.flush()
    for nama, lat, lng in PENERIMA_SEED:
        p = db.query(Penerima).filter_by(nama=nama).one_or_none()
        if p is None:
            p = Penerima(nama=nama)
            db.add(p)
            baru += 1
        p.tipe = TipePenerima.SPPG  # enum tetap (§8.1) — hanya nama yang netral
        p.alamat = f"{nama}, Kota Bandung"
        p.lat = lat
        p.lng = lng
        db.flush()
        if penerima_pertama is None:
            penerima_pertama = p  # Dapur Katering Cibiru — dapur Bu Rina (§8.2)

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
        db.flush()
        if peran is PeranPengguna.PETUGAS:
            # §2.3/§8.1: petugas = petani yang ditunjuk di titik kumpulnya (Asep).
            titik_kumpul.petugas_id = u.id
            db.flush()

    return baru


def _seed_stabil_dari_kode(kode: str) -> int:
    """Seed deterministik dari kode slot — sama di DB mana pun, kapan pun
    (dipakai generator telemetri riwayat: in-loop & backfill menghasilkan
    kurva identik untuk slot yang sama)."""
    return int.from_bytes(uuid.uuid5(uuid.NAMESPACE_DNS, kode).bytes[:2], "big")


def _bangkitkan_telemetri_slot(
    db: Session,
    slot: Slot,
    pengiriman: Pengiriman,
    titik_kumpul: TitikKumpul,
    tujuan_terakhir: Penerima,
    interval: int,
    suhu_dasar: float,
    amplitudo: float,
) -> int:
    """Bangkitkan + simpan telemetri SIMULASI satu pengiriman (idempoten: lewati
    kalau baris sudah ada). Mengembalikan jumlah baris ditambahkan."""
    if db.query(Telemetri).filter_by(pengiriman_id=pengiriman.id).first() is not None:
        return 0
    if pengiriman.waktu_berangkat is None or pengiriman.waktu_tiba is None:
        return 0
    durasi = max(interval, int((pengiriman.waktu_tiba - pengiriman.waktu_berangkat).total_seconds() // 60))
    baris = bangkitkan_telemetri(
        pengiriman_id=pengiriman.id,
        waktu_mulai=pengiriman.waktu_berangkat,
        durasi_menit=durasi,
        interval_menit=interval,
        lat_asal=titik_kumpul.lat,
        lng_asal=titik_kumpul.lng,
        lat_tujuan=tujuan_terakhir.lat,
        lng_tujuan=tujuan_terakhir.lng,
        suhu_dasar_c=float(suhu_dasar),
        amplitudo_suhu_c=float(amplitudo),
        seed=_seed_stabil_dari_kode(slot.kode),
    )
    db.add_all(baris)
    return len(baris)


def seed_telemetri_riwayat(db: Session) -> int:
    """Backfill telemetri untuk slot riwayat yang sudah ada SEBELUM fitur ini
    ada (§8.1: grafik Lacak & kartu Keamanan Pangan tidak kosong). Idempoten."""
    titik_kumpul = db.query(TitikKumpul).filter_by(kode="CKJ").one()
    interval = baca_konfigurasi(db, "interval_telemetri_menit")
    suhu_dasar = baca_konfigurasi(db, "suhu_dasar_c")
    amplitudo = baca_konfigurasi(db, "amplitudo_suhu_c")

    total = 0
    slots = db.query(Slot).filter(Slot.kode.in_(RIWAYAT_SLOT_KODE)).all()
    for slot in slots:
        pengiriman = db.query(Pengiriman).filter_by(slot_id=slot.id).one_or_none()
        if pengiriman is None:
            continue
        tujuan_terakhir_row = max(slot.tujuan, key=lambda t: t.urutan)
        penerima = db.get(Penerima, tujuan_terakhir_row.penerima_id)
        if penerima is None:
            continue
        total += _bangkitkan_telemetri_slot(
            db, slot, pengiriman, titik_kumpul, penerima, interval, suhu_dasar, amplitudo
        )
    return total


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
    petani_by_nama = {u.nama: u for u in db.query(Pengguna).filter(Pengguna.peran.in_([PeranPengguna.PETANI, PeranPengguna.PETUGAS])).all()}
    # K13: petugas = driver Satu Muatan; muatan riwayat pun ditugaskan padanya.
    petugas = db.query(Pengguna).filter_by(peran=PeranPengguna.PETUGAS).order_by(Pengguna.no_hp).first()
    petugas_id = petugas.id if petugas else None
    if petugas_id is not None:
        # Backfill self-healing: muatan yang sudah ada SEBELUM kolom ini lahir
        # (mis. DB dev/produksi yang sudah ter-seed) tetap perlu driver, kalau
        # tidak layar petugas kosong dan otorisasi menolak semuanya.
        db.query(Slot).filter(Slot.petugas_id.is_(None)).update(
            {"petugas_id": petugas_id}, synchronize_session=False
        )
        db.flush()
    tier_row_by_kode = {t.kode: t for t in db.query(TierKendaraan).all()}

    tiers = baca_tiers_aktif(db)
    maks_kendaraan = baca_konfigurasi(db, "maks_kendaraan")
    faktor_jalan = baca_konfigurasi(db, "faktor_jalan")
    kecepatan = baca_konfigurasi(db, "kecepatan_rata_kmh")
    toleransi = baca_konfigurasi(db, "faktor_toleransi_transit")
    ambang_grade = baca_konfigurasi(db, "ambang_grade_asal")
    ambang_paparan = baca_konfigurasi(db, "ambang_paparan_persen")
    # K14 — indeks mutu ikut dicatat di riwayat supaya kartu penerima punya
    # angka historis, bukan hanya untuk kiriman baru.
    bobot_umur = baca_konfigurasi(db, "bobot_mutu_umur_simpan")
    bobot_transit = baca_konfigurasi(db, "bobot_mutu_transit")
    ambang_tolak = baca_konfigurasi(db, "ambang_tolak_persen")
    interval_telemetri = baca_konfigurasi(db, "interval_telemetri_menit")
    suhu_dasar = baca_konfigurasi(db, "suhu_dasar_c")
    amplitudo_suhu = baca_konfigurasi(db, "amplitudo_suhu_c")

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
            # K13: driver yang menangani muatan ini (riwayat pun perlu terisi
            # supaya layar petugas & otorisasi konsisten).
            petugas_id=petugas_id,
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
                # K14: foto muat wajib. Riwayat tidak lewat kamera, jadi diisi
                # gambar pengganti yang jelas-jelas bukan foto asli — supaya
                # Berita Acara riwayat tidak tampil seolah buktinya hilang.
                foto_muat=FOTO_PLACEHOLDER_DEMO,
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
        db.flush()

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
            # K14: tidak ada lagi "terima dengan potongan". Riwayat hanya memuat
            # TERIMA atau TOLAK, dan TOLAK dipakai hemat — hanya pada lot yang
            # memang cacat sejak muat.
            if atribusi_str == Atribusi.PETANI.value and idx % 12 == 11:
                keputusan, alasan = (
                    KeputusanSerahTerima.TOLAK,
                    "Cacat terlihat sejak muat — kualitas tidak layak terima, lot ditolak seluruhnya.",
                )
            elif atribusi_str == Atribusi.PETANI.value:
                keputusan, alasan = (
                    KeputusanSerahTerima.TERIMA,
                    "Cacat terlihat sejak muat; tetap diterima dan dicatat sebagai atribusi petani.",
                )
            elif atribusi_str == Atribusi.LOGISTIK.value:
                keputusan, alasan = (
                    KeputusanSerahTerima.TERIMA,
                    "Transit melebihi ambang waktu rute — diterima, penyusutan dicatat sebagai atribusi logistik.",
                )
            else:
                keputusan, alasan = KeputusanSerahTerima.TERIMA, None

            indeks_mutu = hitung_indeks_mutu(
                sisa_umur_simpan_persen=sisa,
                durasi_transit_menit=durasi,
                ambang_transit_menit=ambang_menit,
                bobot_umur_simpan=bobot_umur,
                bobot_transit=bobot_transit,
                ambang_tolak_persen=ambang_tolak,
            ).indeks_mutu

            db.add(
                SerahTerima(
                    lot_id=lot.id,
                    penerima_id=penerima_tujuan.id,
                    waktu_bongkar=waktu_bongkar,
                    keputusan=keputusan,
                    alasan=alasan,
                    durasi_transit_menit=durasi,
                    ambang_transit_menit=ambang_menit,
                    atribusi=Atribusi(atribusi_str),
                    grade_tiba=grade_tiba,
                    sisa_umur_simpan_persen=sisa,
                    indeks_mutu=indeks_mutu,
                )
            )
            # K14: penolakan bukan "selesai" — riwayat petani harus jujur.
            if keputusan == KeputusanSerahTerima.TOLAK:
                p.status = StatusPartisipasi.DITOLAK
            penerima_volume_terkirim[penerima_tujuan.id] = (
                penerima_volume_terkirim.get(penerima_tujuan.id, 0) + p.volume_kg
            )

        pengiriman.waktu_tiba = max(waktu_bongkar_list)

        # Telemetri SIMULASI untuk slot riwayat (§8.1) — grafik Lacak & kartu
        # Keamanan Pangan tidak kosong saat demo. Seed stabil dari kode slot
        # (identik dengan hasil backfill seed_telemetri_riwayat).
        _bangkitkan_telemetri_slot(
            db, slot, pengiriman, titik_kumpul, tujuan_penerima[-1],
            interval_telemetri, suhu_dasar, amplitudo_suhu,
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
        # K14: daftar wilayah untuk autocomplete alamat — dari berkas JSON di
        # repo, bukan dari jaringan.
        wilayah_baru = seed_wilayah(db)
        riwayat_baru = seed_riwayat(db)
        telemetri_baru = seed_telemetri_riwayat(db)
        db.commit()
        print(
            f"Seed selesai: {tier_baru} tier baru, {konf_baru} konfigurasi baru, "
            f"{induk_baru} data induk baru, {wilayah_baru} wilayah baru, "
            f"{riwayat_baru} slot riwayat baru, "
            f"{telemetri_baru} baris telemetri baru (sisanya di-update/dilewati)."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
