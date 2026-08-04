"""Unduh data wilayah administratif Jawa Barat sekali, simpan sebagai JSON di repo.

DIJALANKAN MANUAL, BUKAN SAAT RUNTIME. Aplikasi tidak boleh memanggil layanan
luar untuk sesuatu sedasar daftar kecamatan — demo harus tetap jalan walau juri
membukanya tanpa internet, dan kuota pihak ketiga bukan urusan pengguna.

Sumber: https://wilayah.id (data Kemendagri, kode wilayah resmi).
Cakupan: provinsi 32 (Jawa Barat), sampai tingkat desa/kelurahan.

    cd backend && python seed/unduh_wilayah.py

Untuk memperluas ke provinsi lain, ubah KODE_PROVINSI dan jalankan lagi.
Berkas keluaran (`seed/data/wilayah_jabar.json`) di-commit — itulah sumber
kebenaran saat seeding, bukan jaringan.
"""

import json
import pathlib
import sys
import time
import urllib.request

KODE_PROVINSI = "32"  # Jawa Barat
BASIS = "https://wilayah.id/api"
TUJUAN = pathlib.Path(__file__).resolve().parent / "data" / "wilayah_jabar.json"
JEDA_DETIK = 0.15  # sopan terhadap layanan gratis


def ambil(path: str) -> list[dict]:
    permintaan = urllib.request.Request(
        f"{BASIS}/{path}", headers={"User-Agent": "SatuMuatan/1.0 (unduh sekali, data disimpan lokal)"}
    )
    with urllib.request.urlopen(permintaan, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["data"]


def main() -> int:
    baris: list[dict] = []

    provinsi = [p for p in ambil("provinces.json") if p["code"] == KODE_PROVINSI]
    if not provinsi:
        print(f"Provinsi {KODE_PROVINSI} tidak ditemukan", file=sys.stderr)
        return 1
    baris.append({"kode": provinsi[0]["code"], "nama": provinsi[0]["name"], "tingkat": "PROVINSI", "induk": None})

    kabupaten = ambil(f"regencies/{KODE_PROVINSI}.json")
    for kab in kabupaten:
        baris.append({"kode": kab["code"], "nama": kab["name"], "tingkat": "KABUPATEN", "induk": KODE_PROVINSI})

    for i, kab in enumerate(kabupaten, 1):
        kecamatan = ambil(f"districts/{kab['code']}.json")
        time.sleep(JEDA_DETIK)
        for kec in kecamatan:
            baris.append({"kode": kec["code"], "nama": kec["name"], "tingkat": "KECAMATAN", "induk": kab["code"]})

        for kec in kecamatan:
            for desa in ambil(f"villages/{kec['code']}.json"):
                baris.append({"kode": desa["code"], "nama": desa["name"], "tingkat": "DESA", "induk": kec["code"]})
            time.sleep(JEDA_DETIK)

        print(f"[{i}/{len(kabupaten)}] {kab['name']} — total {len(baris)} baris", flush=True)

    TUJUAN.parent.mkdir(parents=True, exist_ok=True)
    TUJUAN.write_text(json.dumps(baris, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"OK  {TUJUAN} ({len(baris)} baris)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
