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
    Konfigurasi,
    Koperasi,
    Lot,
    Partisipasi,
    Penerima,
    Pengiriman,
    Permintaan,
    SerahTerima,
    Slot,
    SlotTujuan,
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
        db.query(JejakPosisi).filter(JejakPosisi.pengiriman_id.in_(pengiriman_ids)).delete(synchronize_session=False)
    if lot_ids:
        db.query(Lot).filter(Lot.id.in_(lot_ids)).delete(synchronize_session=False)
    db.query(Pengiriman).filter(~Pengiriman.slot_id.in_(slot_riwayat_ids)).delete(synchronize_session=False)
    db.query(Partisipasi).filter(~Partisipasi.slot_id.in_(slot_riwayat_ids)).delete(synchronize_session=False)
    db.query(SlotTujuan).filter(~SlotTujuan.slot_id.in_(slot_riwayat_ids)).delete(synchronize_session=False)
    db.query(Permintaan).filter(
        (Permintaan.slot_id.is_(None)) | (~Permintaan.slot_id.in_(slot_riwayat_ids))
    ).delete(synchronize_session=False)
    db.query(Slot).filter(~Slot.id.in_(slot_riwayat_ids)).delete(synchronize_session=False)

    _reset_konfigurasi_default(db)
    db.commit()

    return {"slot_riwayat_dipertahankan": len(slot_riwayat_ids)}


# ---------------------------------------------------------------------------
# Cheat-sheet — angka dihitung LIVE, bukan ditulis manual
# ---------------------------------------------------------------------------

# Referensi KEPUTUSAN.md K2 HANYA untuk mencetak status verifikasi di bawah —
# tidak pernah dipakai untuk perhitungan apa pun (mesin harga sungguhan di atas
# yang menghitung; ini cuma pembanding cetak).
_K2_REFERENSI = {
    "jarak_km": 70.03,
    "ambang_menit": 181,
    "atap_asep": 1007,
    "berjalan_wati": 605,
    "berjalan_dedi": 445,
    "berjalan_ijah": 388,
    "tier_final": "VAN",
    "hemat_asep_per_kg": 619,
    "hemat_asep_rp": 185_700,
}


def _rp(n: int) -> str:
    return f"Rp{n:,}".replace(",", ".")


def _cocok(live, referensi, toleransi: float = 0) -> str:
    sama = live == referensi if isinstance(live, str) or isinstance(referensi, str) else abs(live - referensi) <= toleransi
    return "cocok" if sama else f"BERBEDA (live={live}, K2={referensi})"


def bangun_cheat_sheet(db: Session) -> str:
    """Langkah 1-13 (§11.2) dengan angka dihitung ulang live dari mesin harga +
    koordinat seed saat fungsi ini dipanggil — bukan disalin dari dokumen."""
    koperasi = db.query(Koperasi).filter_by(kode="CKJ").one()
    cibiru = db.query(Penerima).filter_by(nama="SPPG Cibiru 3").one()
    ujungberung = db.query(Penerima).filter_by(nama="SPPG Ujungberung 1").one()
    panyileukan = db.query(Penerima).filter_by(nama="SPPG Panyileukan 2").one()

    tiers = baca_tiers_aktif(db)
    maks_kendaraan = baca_konfigurasi(db, "maks_kendaraan")
    faktor_jalan = baca_konfigurasi(db, "faktor_jalan")
    kecepatan = baca_konfigurasi(db, "kecepatan_rata_kmh")
    toleransi_transit = baca_konfigurasi(db, "faktor_toleransi_transit")

    tujuan_input = [
        TujuanInput(penerima_id=cibiru.id, lat=cibiru.lat, lng=cibiru.lng),
        TujuanInput(penerima_id=ujungberung.id, lat=ujungberung.lat, lng=ujungberung.lng),
        TujuanInput(penerima_id=panyileukan.id, lat=panyileukan.lat, lng=panyileukan.lng),
    ]
    urutan = urutkan_tujuan_nearest_neighbor((koperasi.lat, koperasi.lng), tujuan_input, faktor_jalan)
    jarak_km = sum(t.jarak_segmen_km for t in urutan)
    ambang_menit = ambang_transit_menit(jarak_km, kecepatan, toleransi_transit)

    nama_by_id = {cibiru.id: cibiru.nama, ujungberung.id: ujungberung.nama, panyileukan.id: panyileukan.nama}
    rute_teks = " -> ".join(["Gudang koperasi"] + [nama_by_id[t.penerima_id] for t in urutan])

    # Volume individual PERSIS spec §11.2 asli (300 / +200 / +180 / +100 kg),
    # kumulatif 300/500/680/780 — HARGA yang berubah karena rute dikoreksi K2
    # (70,03 km, bukan 84 km), bukan volumenya.
    langkah_petani = [("Asep", 300), ("Wati", 200), ("Dedi", 180), ("Ijah", 100)]
    kumulatif = 0
    atap_by_nama: dict[str, int] = {}
    baris_kaskade: list[tuple[str, int, int, int]] = []  # nama, volume_step, kumulatif, harga_berjalan
    for nama, vol in langkah_petani:
        atap_by_nama[nama] = harga_atap_per_kg(vol, jarak_km, tiers, maks_kendaraan)
        kumulatif += vol
        hb = harga_berjalan_per_kg(kumulatif, jarak_km, tiers, maks_kendaraan)
        baris_kaskade.append((nama, vol, kumulatif, hb))

    partisipasi_final = [
        PartisipasiHarga(id=uuid.uuid4(), volume_kg=vol, harga_atap_per_kg=atap_by_nama[nama])
        for nama, vol in langkah_petani
    ]
    hasil = tetapkan_harga_final(partisipasi_final, jarak_km, tiers, maks_kendaraan)
    tier_ringkas = "+".join(t.kode for t in hasil.rencana.tier)
    hemat_asep_per_kg = atap_by_nama["Asep"] - hasil.harga_final_per_kg
    hemat_asep_rp = hemat_asep_per_kg * langkah_petani[0][1]

    L = []
    add = L.append
    add("=" * 78)
    add("CHEAT-SHEET SKENARIO DEMO (spec 11.2) -- angka DIHITUNG LIVE oleh mesin harga")
    add("Sumber koefisien: tabel konfigurasi & tier_kendaraan pada saat script ini")
    add("dijalankan (bukan hardcoded). Referensi resmi: KEPUTUSAN.md K2.")
    add("=" * 78)
    add("")
    add(f"Rute demo (nearest-neighbor, faktor_jalan={faktor_jalan}): {rute_teks}")
    add(f"  jarak_km = {round(jarak_km, 4)}  [{_cocok(round(jarak_km, 2), _K2_REFERENSI['jarak_km'], 0.01)} vs K2]")
    add(f"  ambang_transit_menit = {ambang_menit}  [{_cocok(ambang_menit, _K2_REFERENSI['ambang_menit'])} vs K2]")
    add("")
    add("Langkah 1. Login Kepala Dapur SPPG Cibiru 3 -> input permintaan 300 kg Kubis, besok.")
    add("")
    add(
        f"Langkah 2. Login Koperasi -> buka slot, pilih 3 tujuan (Cibiru 3, Ujungberung 1, "
        f"Panyileukan 2)."
    )
    add(f"  -> jarak rute = {round(jarak_km, 2)} km; pratinjau kalau 300 kg = {_rp(atap_by_nama['Asep'])}/kg")
    add("")
    add(f"Langkah 3. Petani Asep ikut kirim 300 kg Kubis.")
    add(f"  -> HARGA ATAP TERKUNCI Asep = {_rp(atap_by_nama['Asep'])}/kg  "
        f"[{_cocok(atap_by_nama['Asep'], _K2_REFERENSI['atap_asep'])} vs K2]")
    add("")
    for i, (nama, vol, kum, hb) in enumerate(baris_kaskade[1:], start=4):
        ref_key = {"Wati": "berjalan_wati", "Dedi": "berjalan_dedi", "Ijah": "berjalan_ijah"}[nama]
        add(f"Langkah {i}. Petani {nama} ikut +{vol} kg (kumulatif {kum} kg).")
        add(f"  -> harga berjalan turun ke {_rp(hb)}/kg  [{_cocok(hb, _K2_REFERENSI[ref_key])} vs K2]  [animasi]")
        add("")
    add(f"  -> Layar Asep menunjukkan: \"Kamu hemat {_rp(hemat_asep_per_kg)}/kg -> {_rp(hemat_asep_rp)}\"")
    add(f"    [{_cocok(hemat_asep_per_kg, _K2_REFERENSI['hemat_asep_per_kg'])} vs K2 per-kg, "
        f"{_cocok(hemat_asep_rp, _K2_REFERENSI['hemat_asep_rp'])} vs K2 total]")
    add("")
    add(f"Langkah 7. Koperasi tutup slot -> sistem memilih {tier_ringkas} untuk {kumulatif} kg total.")
    add(f"  [{_cocok(tier_ringkas, _K2_REFERENSI['tier_final'])} vs K2 (VAN untuk 780 kg)]")
    add(f"  harga_final_per_kg = {_rp(hasil.harga_final_per_kg)}, biaya_total = {_rp(hasil.biaya_total)}, "
        f"subsidi_koperasi = {_rp(hasil.subsidi_koperasi)}")
    if hasil.subsidi_koperasi < 0:
        add("  (subsidi negatif = surplus kecil akibat pembulatan ke atas/ceil per partisipan, bukan bug)")
    add("")
    add("Langkah 8. Muat: timbang 4 lot, foto, tandai 1 lot 'ada cacat terlihat'.")
    add("Langkah 9. Lacak: maju status pengiriman sampai TIBA.")
    add(
        f"Langkah 10. Serah terima: 3 lot TERIMA, 1 lot POTONG 20% -> atribusi PETANI "
        f"(cacat terlihat sejak muat, ambang rute ini {ambang_menit} menit)."
    )
    add("Langkah 11. Buka Berita Acara -> cetak (window.print()).")
    add("Langkah 12. Buka Dashboard Dampak -> 4 kartu terisi (8 slot riwayat + 1 slot demo baru).")
    add("Langkah 13. Buka Panel Asumsi -> ubah faktor emisi -> tunjukkan dashboard ikut berubah.")
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
