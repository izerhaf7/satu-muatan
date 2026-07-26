"""Seed: konfigurasi + tier_kendaraan (Fase 0, spec §4.2 + KEPUTUSAN.md K6),
plus data induk (koperasi, penerima, komoditas, pengguna K9) untuk Fase 2.

IDEMPOTEN: upsert per kunci alami — aman dijalankan berulang (DoD §14).
Riwayat 8 slot SELESAI + skenario demo ditambahkan agent infra-demo di Fase 3.

Jalankan dari folder backend:  python seed/seed.py
"""

import pathlib
import sys
from decimal import Decimal

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session  # noqa: E402

from app.auth import hash_pin  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Komoditas,
    Konfigurasi,
    Koperasi,
    Penerima,
    Pengguna,
    PeranPengguna,
    StatusSumber,
    TierKendaraan,
    TipeKonfigurasi,
    TipePenerima,
)

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

CATATAN_KOMODITAS = "Harga acuan perkiraan tim; WAJIB diganti data PIHPS sebelum final (spec §11.1)."

# nama, harga_acuan, umur_simpan_jam, laju_susut_per_jam
KOMODITAS_SEED = [
    ("Kubis", 3_000, 168, Decimal("0.00250")),
    ("Tomat", 5_000, 96, Decimal("0.00520")),
    ("Sawi hijau", 4_000, 48, Decimal("0.00830")),
    ("Wortel", 6_000, 240, Decimal("0.00180")),
]

# nama, lat, lng
PENERIMA_SEED = [
    ("SPPG Cibiru 3", -6.9269, 107.7189),
    ("SPPG Ujungberung 1", -6.9147, 107.7000),
    ("SPPG Panyileukan 2", -6.9333, 107.6989),
]

# K9 — akun kanonik. (nama, no_hp, peran)
PENGGUNA_SEED = [
    ("Bu Nia", "081200000001", PeranPengguna.KOPERASI),
    ("Asep", "081200000011", PeranPengguna.PETANI),
    ("Wati", "081200000012", PeranPengguna.PETANI),
    ("Dedi", "081200000013", PeranPengguna.PETANI),
    ("Ijah", "081200000014", PeranPengguna.PETANI),
    ("Ujang", "081200000015", PeranPengguna.PETANI),
    ("Euis", "081200000016", PeranPengguna.PETANI),
    ("Bu Rina", "081200000021", PeranPengguna.PENERIMA),
]

PIN_DEMO = "123456"


def seed_induk(db: Session) -> int:
    baru = 0

    koperasi = db.query(Koperasi).filter_by(kode="CKJ").one_or_none()
    if koperasi is None:
        koperasi = Koperasi(kode="CKJ")
        db.add(koperasi)
        baru += 1
    koperasi.nama = "Koperasi Desa Mekarjaya"
    koperasi.desa = "Mekarjaya"
    koperasi.kecamatan = "Cikajang"
    koperasi.kabupaten = "Garut"
    koperasi.alamat_gudang = "Jl. Raya Cikajang No. 12, Desa Mekarjaya"
    koperasi.lat = -7.3661  # ASUMSI — perkiraan lokasi gudang (spec §11.1)
    koperasi.lng = 107.7961
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

    for nama, harga, umur, laju in KOMODITAS_SEED:
        k = db.query(Komoditas).filter_by(nama=nama).one_or_none()
        if k is None:
            k = Komoditas(nama=nama)
            db.add(k)
            baru += 1
        k.satuan = "kg"
        k.harga_acuan_per_kg = harga
        k.umur_simpan_jam = umur
        k.laju_susut_per_jam = laju
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
        u.koperasi_id = koperasi.id if peran in (PeranPengguna.KOPERASI, PeranPengguna.PETANI) else None
        u.penerima_id = penerima_pertama.id if peran is PeranPengguna.PENERIMA else None

    return baru


def main() -> None:
    db = SessionLocal()
    try:
        tier_baru = seed_tier(db)
        konf_baru = seed_konfigurasi(db)
        induk_baru = seed_induk(db)
        db.commit()
        print(
            f"Seed selesai: {tier_baru} tier baru, {konf_baru} konfigurasi baru, "
            f"{induk_baru} data induk baru (sisanya di-update)."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
