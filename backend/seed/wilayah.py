"""Seed tabel `wilayah` dari berkas JSON di repo (K14).

Sumber: `seed/data/wilayah_jabar.json`, hasil `seed/unduh_wilayah.py` (data
Kemendagri via wilayah.id). Jaringan TIDAK disentuh di sini — demo harus tetap
jalan tanpa internet.

Koordinat: sumber resmi tidak menyertakannya. Beberapa kecamatan di koridor demo
(Garut → Bandung) diisi manual di `KOORDINAT_KECAMATAN` supaya peta bisa
melompat saat pengguna memilih daerahnya; sisanya tetap berguna untuk melengkapi
alamat walau tanpa koordinat.
"""

import json
import pathlib

from sqlalchemy.orm import Session

from app.models import Wilayah

BERKAS = pathlib.Path(__file__).resolve().parent / "data" / "wilayah_jabar.json"

# Koordinat pusat kecamatan di koridor demo — cukup untuk melompatkan peta ke
# daerah yang dipilih, bukan untuk menentukan titik persis (itu tugas pin).
# Sengaja hanya koridor demo: menebak 627 titik akan jadi data karangan.
# Kode DIVERIFIKASI terhadap `data/wilayah_jabar.json`, bukan ditebak — enam
# tebakan awal ternyata menunjuk kecamatan yang sama sekali lain (mis. kode yang
# dikira Cibiru sebenarnya Kiaracondong), dan reverse geocoding lokal ikut salah.
KOORDINAT_KECAMATAN: dict[str, tuple[float, float]] = {
    "32.05.22": (-7.3661, 107.7961),  # Cikajang, Kab. Garut — titik kumpul demo
    "32.05.01": (-7.2145, 107.9080),  # Garut Kota
    "32.05.04": (-7.1900, 107.8800),  # Tarogong Kaler
    "32.05.05": (-7.2100, 107.8850),  # Tarogong Kidul
    "32.05.07": (-7.2350, 107.8100),  # Samarang
    "32.04.12": (-6.9800, 107.6200),  # Dayeuhkolot, Kab. Bandung
    "32.04.37": (-7.0300, 107.5200),  # Soreang, Kab. Bandung
    "32.04.05": (-6.9400, 107.7550),  # Cileunyi, Kab. Bandung
    "32.73.25": (-6.9269, 107.7189),  # Cibiru, Kota Bandung
    "32.73.26": (-6.9147, 107.7000),  # Ujungberung, Kota Bandung
    "32.73.28": (-6.9333, 107.6989),  # Panyileukan, Kota Bandung
    "32.73.13": (-6.9250, 107.6250),  # Lengkong, Kota Bandung
    "32.73.16": (-6.9200, 107.6450),  # Kiaracondong, Kota Bandung
}


def _muat_baris() -> list[dict]:
    if not BERKAS.exists():
        return []
    return json.loads(BERKAS.read_text(encoding="utf-8"))


def seed_wilayah(db: Session) -> int:
    """Isi tabel `wilayah`. Idempoten — baris yang sudah ada dilewati.

    Mengembalikan jumlah baris baru. Kalau berkas datanya tidak ada, kembalikan
    0 tanpa melempar galat: autocomplete jadi kosong, tapi tidak ada satu pun
    alur yang mati karenanya."""
    baris = _muat_baris()
    if not baris:
        return 0

    sudah_ada = {k for (k,) in db.query(Wilayah.kode).all()}
    nama_by_kode = {b["kode"]: b["nama"] for b in baris}

    # Koordinat di sini adalah SATU-SATUNYA sumber kebenaran koordinat wilayah.
    # Bersihkan dulu yang di luar daftar: koreksi kode yang keliru pernah
    # meninggalkan koordinat basi menempel di kecamatan lain, dan reverse
    # geocoding lokal jadi menunjuk daerah yang salah.
    db.query(Wilayah).filter(Wilayah.kode.notin_(list(KOORDINAT_KECAMATAN))).update(
        {"lat": None, "lng": None}, synchronize_session=False
    )

    def jalur(b: dict) -> str:
        """Nama berjenjang siap tampil, mis. 'Cikajang, Kabupaten Garut, Jawa Barat'."""
        bagian = [b["nama"]]
        induk = b.get("induk")
        while induk:
            if induk not in nama_by_kode:
                break
            bagian.append(nama_by_kode[induk])
            # Naik satu tingkat: kode induk adalah awalan kode anak.
            induk = ".".join(induk.split(".")[:-1]) or None
        return ", ".join(bagian)

    baru = 0
    for b in baris:
        koordinat = KOORDINAT_KECAMATAN.get(b["kode"])
        if b["kode"] in sudah_ada:
            # Koordinat adalah lapisan kurasi kita sendiri dan bisa dikoreksi;
            # segarkan walau barisnya sudah ada, supaya perbaikan benar-benar
            # sampai ke database tanpa perlu mengosongkan tabel.
            if koordinat is not None:
                db.query(Wilayah).filter_by(kode=b["kode"]).update(
                    {"lat": koordinat[0], "lng": koordinat[1]}, synchronize_session=False
                )
            continue
        db.add(
            Wilayah(
                kode=b["kode"],
                nama=b["nama"],
                tingkat=b["tingkat"],
                induk_kode=b.get("induk"),
                jalur=jalur(b),
                lat=koordinat[0] if koordinat else None,
                lng=koordinat[1] if koordinat else None,
            )
        )
        baru += 1
    db.commit()
    return baru


if __name__ == "__main__":  # pragma: no cover
    import sys

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    from app.database import SessionLocal

    with SessionLocal() as sesi:
        print(f"wilayah: {seed_wilayah(sesi)} baris baru")
