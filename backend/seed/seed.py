"""Seed Fase 0: konfigurasi + tier_kendaraan (spec §4.2 + KEPUTUSAN.md K6).

IDEMPOTEN: upsert per kunci/kode — aman dijalankan berulang (DoD §14).
Seed lengkap demo (koperasi, pengguna, penerima, komoditas, riwayat 8 slot)
ditambahkan agent infra-demo di Fase 3, di file ini juga, dengan pola sama.

Jalankan dari folder backend:  python seed/seed.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sqlalchemy.orm import Session  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import Konfigurasi, StatusSumber, TierKendaraan, TipeKonfigurasi  # noqa: E402

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


def main() -> None:
    db = SessionLocal()
    try:
        tier_baru = seed_tier(db)
        konf_baru = seed_konfigurasi(db)
        db.commit()
        print(f"Seed selesai: {tier_baru} tier baru, {konf_baru} konfigurasi baru (sisanya di-update).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
