"""Skenario demo (spec §11.2, KEPUTUSAN.md K2) — SATU perintah mengembalikan DB
ke keadaan awal PERSIS demo: data transaksional dikosongkan KECUALI 8 slot riwayat
(`seed.seed.RIWAYAT_SLOT_KODE`, tetap — sumber grafik Dashboard Dampak), master
data + tier tetap utuh, dan `konfigurasi` dipaksa kembali ke nilai default seed
(perubahan lewat Panel Asumsi saat gladi bersih TIDAK boleh terbawa ke sesi demo
berikutnya).

Fungsi `reset_ke_awal_demo()` di bawah dipakai oleh DUA pintu masuk yang wajib
berperilaku identik:
  1. CLI: `python seed/skenario_demo.py` (script ini, mencetak cheat-sheet)
  2. API: `POST /api/demo/reset` (`app/routers/demo.py`, DEMO_MODE only)

Angka di cheat-sheet TIDAK PERNAH ditulis manual — semuanya dipanggil live dari
`app.domain.armada/harga/atribusi` dengan koefisien dibaca dari tabel `konfigurasi`
saat script dijalankan (CLAUDE.md aturan #1). Referensi KEPUTUSAN.md K2 di bagian
bawah file ini HANYA dipakai untuk mencetak status verifikasi (cocok/berbeda),
bukan untuk perhitungan.

Jalankan dari folder backend:  python seed/skenario_demo.py
"""

import pathlib
import sys
import uuid
from datetime import datetime, timezone

_BACKEND_DIR = pathlib.Path(__file__).resolve().parents[1]
_SELF_DIR = pathlib.Path(__file__).resolve().parent  # backend/seed

# Saat dijalankan langsung (`python seed/skenario_demo.py`), Python otomatis
# menaruh folder skrip ini (backend/seed/) di sys.path[0] — itu bentrok dengan
# `seed.py` di folder yang SAMA: `import seed` lalu resolve ke FILE
# backend/seed/seed.py (bukan PACKAGE backend/seed), sehingga `from seed.seed
# import ...` di bawah gagal ("'seed' is not a package"). Buang dulu entri itu
# supaya backend/ (yang disisipkan berikutnya) yang menang saat resolusi paket.
while str(_SELF_DIR) in sys.path:
    sys.path.remove(str(_SELF_DIR))
sys.path.insert(0, str(_BACKEND_DIR))

from sqlalchemy.orm import Session  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.domain.armada import TujuanInput, urutkan_tujuan_nearest_neighbor  # noqa: E402
from app.domain.atribusi import ambang_transit_menit  # noqa: E402
from app.domain.harga import PartisipasiHarga, harga_atap_per_kg, harga_berjalan_per_kg, tetapkan_harga_final  # noqa: E402
from app.models import (  # noqa: E402
    JejakPosisi,
    Kiriman,
    Komoditas,
    Konfigurasi,
    Lot,
    Partisipasi,
    Penerima,
    Pengiriman,
    SerahTerima,
    Slot,
    SlotJemput,
    SlotTujuan,
    Telemetri,
    TitikKumpul,
)
from app.services.konfigurasi import baca_konfigurasi, baca_tiers_aktif  # noqa: E402
from seed.seed import (  # noqa: E402
    KONFIGURASI_SEED,
    RIWAYAT_SLOT_KODE,
    seed_induk,
    seed_konfigurasi,
    seed_riwayat,
    seed_tier,
)

# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


def _reset_konfigurasi_default(db: Session) -> None:
    """Beda dari `seed_konfigurasi()` (yang sengaja TIDAK menimpa `nilai` supaya
    perubahan Panel Asumsi selamat dari `seed/seed.py` berulang): di sini `nilai`
    DIPAKSA kembali ke default — reset demo berarti kembali ke titik nol, termasuk
    eksperimen Panel Asumsi di langkah 13 (§11.2)."""
    for kunci, nilai, tipe, label, satuan, status, catatan in KONFIGURASI_SEED:
        konf = db.get(Konfigurasi, kunci)
        if konf is None:
            konf = Konfigurasi(kunci=kunci, nilai=nilai)
            db.add(konf)
        konf.nilai = nilai
        konf.tipe = tipe
        konf.label = label
        konf.satuan = satuan
        konf.status_sumber = status
        konf.catatan_sumber = catatan


def reset_ke_awal_demo(db: Session) -> dict[str, int]:
    """Satu fungsi dipakai CLI & `POST /api/demo/reset`. Urutan:

    1. Pastikan baseline ada (tier, metadata konfigurasi, induk, 8 slot riwayat) —
       idempoten dan murah, jadi aman dipanggil tiap reset (self-healing kalau
       ada yang kebetulan hilang saat gladi bersih).
    2. Hapus SEMUA data transaksional KECUALI 8 slot riwayat (anak sebelum induk,
       mengikuti urutan FK — sama seperti `demo.py` sebelum refactor ini).
    3. Paksa nilai `konfigurasi` kembali ke default seed.

    Deterministik, idempoten: dipanggil berkali-kali menghasilkan keadaan yang
    sama persis.
    """
    seed_tier(db)
    seed_konfigurasi(db)
    seed_induk(db)
    db.commit()
    seed_riwayat(db)
    db.commit()

    slot_riwayat_ids = [row[0] for row in db.query(Slot.id).filter(Slot.kode.in_(RIWAYAT_SLOT_KODE)).all()]

    lot_ids = [
        row[0]
        for row in db.query(Lot.id)
        .join(Partisipasi, Partisipasi.id == Lot.partisipasi_id)
        .filter(~Partisipasi.slot_id.in_(slot_riwayat_ids))
        .all()
    ]
    pengiriman_ids = [row[0] for row in db.query(Pengiriman.id).filter(~Pengiriman.slot_id.in_(slot_riwayat_ids)).all()]

    # Urutan wajib mengikuti dependensi FK (anak sebelum induk).
    if lot_ids:
        db.query(SerahTerima).filter(SerahTerima.lot_id.in_(lot_ids)).delete(synchronize_session=False)
    if pengiriman_ids:
        db.query(Telemetri).filter(Telemetri.pengiriman_id.in_(pengiriman_ids)).delete(synchronize_session=False)
        db.query(JejakPosisi).filter(JejakPosisi.pengiriman_id.in_(pengiriman_ids)).delete(synchronize_session=False)
    if lot_ids:
        db.query(Lot).filter(Lot.id.in_(lot_ids)).delete(synchronize_session=False)
    # Kiriman (v2 §3) — tidak ada di slot riwayat, jadi selalu ikut dibersihkan.
    db.query(Kiriman).delete(synchronize_session=False)
    db.query(Pengiriman).filter(~Pengiriman.slot_id.in_(slot_riwayat_ids)).delete(synchronize_session=False)
    # K14: `slot_jemput` mereferensikan `partisipasi`, jadi WAJIB dihapus lebih
    # dulu — tanpa ini reset demo gagal dengan ForeignKeyViolation.
    db.query(SlotJemput).filter(~SlotJemput.slot_id.in_(slot_riwayat_ids)).delete(synchronize_session=False)
    db.query(Partisipasi).filter(~Partisipasi.slot_id.in_(slot_riwayat_ids)).delete(synchronize_session=False)
    db.query(SlotTujuan).filter(~SlotTujuan.slot_id.in_(slot_riwayat_ids)).delete(synchronize_session=False)
    db.query(Slot).filter(~Slot.id.in_(slot_riwayat_ids)).delete(synchronize_session=False)
    # K13: buang alamat tujuan bentukan sistem dari sesi demo sebelumnya, supaya
    # buku alamat tidak menggelembung tiap kali demo diulang. Baris seed
    # (dibuat_otomatis=False) selalu dipertahankan.
    db.query(Penerima).filter(Penerima.dibuat_otomatis.is_(True)).delete(synchronize_session=False)

    _reset_konfigurasi_default(db)
    db.commit()

    return {"slot_riwayat_dipertahankan": len(slot_riwayat_ids)}


# ---------------------------------------------------------------------------
# Cheat-sheet — angka dihitung LIVE, bukan ditulis manual (v2 §8.2)
# ---------------------------------------------------------------------------


def _rp(n: int) -> str:
    return f"Rp{n:,}".replace(",", ".")


def bangun_cheat_sheet(db: Session) -> str:
    """Langkah 1–10 (v2 §8.2) — semua angka dihitung ulang live dari mesin harga,
    generator telemetri, dan model Q10 saat fungsi ini dipanggil. Jangan salin
    angka dari dokumen ke kode; kalau hasil mesin berbeda dari catatan demo,
    perbarui catatannya (§4.3)."""
    from app.domain.paparan import hitung_paparan
    from app.services import mesin
    from app.services.telemetri import bangkitkan_telemetri, sampel_domain_dari_baris

    titik_kumpul = db.query(TitikKumpul).filter_by(kode="CKJ").one()
    cibiru = db.query(Penerima).filter_by(nama="Dapur Katering Cibiru").one()
    sawi = db.query(Komoditas).filter_by(nama="Sawi hijau").one()

    tiers = baca_tiers_aktif(db)
    maks_kendaraan = baca_konfigurasi(db, "maks_kendaraan")
    faktor_jalan = baca_konfigurasi(db, "faktor_jalan")
    kecepatan = baca_konfigurasi(db, "kecepatan_rata_kmh")
    toleransi_transit = baca_konfigurasi(db, "faktor_toleransi_transit")
    interval = baca_konfigurasi(db, "interval_telemetri_menit")
    suhu_dasar = baca_konfigurasi(db, "suhu_dasar_c")
    amplitudo = baca_konfigurasi(db, "amplitudo_suhu_c")

    # Rute muatan demo: SATU tujuan (alur kiriman §3) — titik kumpul → Cibiru.
    jarak_km = mesin.jarak_haversine_km(titik_kumpul.lat, titik_kumpul.lng, cibiru.lat, cibiru.lng) * faktor_jalan
    ambang_menit = ambang_transit_menit(jarak_km, kecepatan, toleransi_transit)

    langkah_petani = [("Bu Nia", 300), ("Wati", 200), ("Dedi", 180), ("Ijah", 100)]
    kumulatif = 0
    atap_by_nama: dict[str, int] = {}
    baris_kaskade: list[tuple[str, int, int, int]] = []
    for nama, vol in langkah_petani:
        atap_by_nama[nama] = harga_atap_per_kg(vol, jarak_km, tiers, maks_kendaraan)
        kumulatif += vol
        baris_kaskade.append((nama, vol, kumulatif, harga_berjalan_per_kg(kumulatif, jarak_km, tiers, maks_kendaraan)))

    potensi_pratinjau = harga_berjalan_per_kg(300 * 4, jarak_km, tiers, maks_kendaraan)

    partisipasi_final = [
        PartisipasiHarga(id=uuid.uuid4(), volume_kg=vol, harga_atap_per_kg=atap_by_nama[nama])
        for nama, vol in langkah_petani
    ]
    hasil = tetapkan_harga_final(partisipasi_final, jarak_km, tiers, maks_kendaraan)
    tier_ringkas = "+".join(t.kode for t in hasil.rencana.tier)
    hemat_bu_nia_per_kg = atap_by_nama["Bu Nia"] - hasil.harga_final_per_kg
    hemat_bu_nia_rp = hemat_bu_nia_per_kg * langkah_petani[0][1]

    # Simulasi telemetri perjalanan siang (berangkat 13.00 WIB, 3 jam) → angka
    # kartu suhu & sisa umur simpan sawi (q10 dari tabel komoditas).
    berangkat_demo = datetime(2026, 8, 2, 6, 0, tzinfo=timezone.utc)  # 13.00 WIB
    sampel = bangkitkan_telemetri(
        pengiriman_id=uuid.uuid4(),
        waktu_mulai=berangkat_demo,
        durasi_menit=180,
        interval_menit=interval,
        lat_asal=titik_kumpul.lat,
        lng_asal=titik_kumpul.lng,
        lat_tujuan=cibiru.lat,
        lng_tujuan=cibiru.lng,
        suhu_dasar_c=float(suhu_dasar),
        amplitudo_suhu_c=float(amplitudo),
        seed=42,
    )
    paparan = hitung_paparan(
        sampel_domain_dari_baris(sampel), float(sawi.q10), float(sawi.suhu_acuan_c), sawi.umur_simpan_jam
    )

    L = []
    add = L.append
    add("=" * 78)
    add("CHEAT-SHEET SKENARIO DEMO v4 (K14) -- angka DIHITUNG LIVE oleh mesin")
    add("Sumber koefisien: tabel konfigurasi, tier_kendaraan & komoditas saat script")
    add("ini dijalankan (bukan hardcoded). Kalau beda dari catatan demo, mesin yang benar.")
    add("=" * 78)
    add("")
    add(f"Muatan demo (satu tujuan, alur Kirim Panen): {titik_kumpul.nama} -> {cibiru.nama}")
    add(f"  jarak_km = {round(jarak_km, 2)} · ambang_transit_menit = {ambang_menit}")
    add("")
    add("Langkah 1. Login Petani Bu Nia -> \"Kirim Panen\". Tandai TITIK JEMPUT (tombol")
    add("   'Gunakan lokasi saya' / ketuk peta -> alamat terbaca otomatis; ketik nama")
    add("   desa untuk autocomplete daerah), lalu TUJUAN dengan cara yang sama.")
    add("   Volume di bawah 50 kg ditolak DI LAYAR, bukan setelah dikirim.")
    add("   Tujuan Dapur Katering Cibiru, sawi,")
    add(f"   300 kg, besok -> atap {_rp(atap_by_nama['Bu Nia'])}/kg, potensi ± {_rp(potensi_pratinjau)}/kg")
    add("")
    add("Langkah 2. Kirim -> sistem buka muatan baru -> layar \"Muatanmu\" (Detail Slot).")
    add("")
    add("Langkah 3. Login Petani Wati -> kirim 200 kg, tujuan 8 km dari tujuan Bu Nia")
    add(f"   (radius koridor 15 km) -> muatan SAMA -> harga berjalan turun ke {_rp(baris_kaskade[1][3])}/kg [animasi]")
    add("")
    add(f"Langkah 4. Dedi +180 kg (kumulatif {baris_kaskade[2][2]} kg) -> {_rp(baris_kaskade[2][3])}/kg [animasi]")
    add(f"           Ijah +100 kg (kumulatif {baris_kaskade[3][2]} kg) -> {_rp(baris_kaskade[3][3])}/kg [animasi]")
    add(
        f"   Layar Bu Nia: \"Atap {_rp(atap_by_nama['Bu Nia'])} (terkunci). Sekarang {_rp(hasil.harga_final_per_kg)}. "
        f"Hemat {_rp(hemat_bu_nia_rp)}.\""
    )
    add("")
    add("Langkah 5. Login Petugas -> Beranda: muatan menunggu di PAPAN TUGAS.")
    add("   Tekan 'Ambil tugas ini'. Mengambil muatan kedua -> DITOLAK (batas 1 aktif).")
    add(f"   Tutup muatan -> sistem memilih {tier_ringkas} untuk {kumulatif} kg.")
    add(f"   biaya_total = {_rp(hasil.biaya_total)}, selisih_jaminan_atap = {_rp(hasil.subsidi_koperasi)}")
    add("   Muat: RUTE PENJEMPUTAN berurutan tampil (nomor, petani, alamat, jarak,")
    add("   tombol arah jalan). Timbang tiap lot -- FOTO MUAT WAJIB, tombol simpan")
    add("   terkunci tanpa foto. Grade mutu: 3 lot \"Sangat baik\", 1 lot \"Cukup\".")
    add("")
    add("Langkah 6. Berangkat -> Lacak: tekan 'Majukan posisi' atau nyalakan 'Jalan")
    add("   otomatis' -- peta benar-benar bergerak sepanjang rute.")
    add("   Grafik suhu naik siang hari (label 'Data simulasi').")
    add(
        f"   Kartu: suhu maks {paparan.suhu_maks_c:.1f} °C, suhu rata-rata {paparan.suhu_rata_c:.1f} °C, "
        f"sisa umur simpan {paparan.sisa_umur_simpan_persen}%"
    )
    add("")
    add("Langkah 7. Serah Terima: penerima melihat GRAFIK PERJALANAN + INDEKS MUTU dulu,")
    add("   baru memutuskan. Pilihannya hanya TERIMA atau TOLAK -- tidak ada potongan")
    add("   harga (K14). Tombol Tolak baru muncul kalau penurunan mutu yang diukur")
    add("   sistem melewati ambang; server ikut menolak permintaan yang tidak memenuhi.")
    add("   Lot bergrade asal di bawah standar -> atribusi PETANI + kalimat penjelasan.")
    add("Langkah 8. Riwayat petani: tiap baris BISA DIKLIK, dengan tautan Lacak &")
    add("   Berita Acara -> cetak (window.print()).")
    add("Langkah 9. Dashboard Dampak -> EMPAT kartu semboyan terisi (8 slot riwayat + demo).")
    add("Langkah 10. Panel Asumsi -> ubah faktor emisi -> kartu emisi ikut berubah.")
    add("")
    add("=" * 78)
    return "\n".join(L)


def main() -> None:
    # Jaga-jaga: konsol Windows default ke cp1252 (tidak mendukung sebagian
    # karakter unicode) — paksa UTF-8 di stdout supaya cheat-sheet tidak pernah
    # crash gara-gara encoding, di terminal mana pun script ini dijalankan.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    db = SessionLocal()
    try:
        stats = reset_ke_awal_demo(db)
        print(
            f"Reset selesai: DB dikembalikan ke keadaan awal skenario demo. "
            f"Slot riwayat dipertahankan: {stats['slot_riwayat_dipertahankan']}. "
            f"Konfigurasi dikembalikan ke default seed."
        )
        print()
        print(bangun_cheat_sheet(db))
    finally:
        db.close()


if __name__ == "__main__":
    main()
