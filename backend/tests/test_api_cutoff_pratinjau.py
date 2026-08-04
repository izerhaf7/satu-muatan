"""Regresi K14 — cutoff yang bermakna & pratinjau harga yang jujur.

Dua cacat yang ditutup di sini:

1. **Cutoff cuma hiasan.** `cutoff_at` dihitung H-1 jam 18 WIB, jadi kiriman
   untuk besok yang dibuat malam hari lahir dengan cutoff SUDAH LEWAT — layar
   langsung menulis "sudah ditutup" pada muatan yang baru saja dibuka. Lebih
   buruk lagi, muatan lewat cutoff tetap menyerap kiriman baru tanpa batas.

2. **Pratinjau berbohong.** Simulasi `_cek_gabung` menerima objek penerima dan
   menyaring tujuannya lewat query id. Pada pratinjau id itu `None`, sehingga
   tujuan calon HILANG dari simulasi: jarak (dan harga) yang dilaporkan adalah
   jarak muatan lama, tanpa memperhitungkan belokan menuju alamat petani.
"""

from datetime import date, datetime, timedelta, timezone

import pytest

from app.models import Slot
from app.models.enums import StatusSlot

# Tujuan berjauhan supaya belokan menuju tujuan kedua benar-benar menambah rute.
TUJUAN_A = (-6.9269, 107.7189)
TUJUAN_B = (-6.9800, 107.6200)


@pytest.fixture()
def besok() -> date:
    return date.today() + timedelta(days=1)


def test_cutoff_baru_tidak_pernah_lahir_di_masa_lalu(client, data_dasar, masuk, kirim_panen, besok, db):
    """Jadwal normal H-1 18:00 WIB sering sudah lewat; muatan baru tetap harus
    memberi jeda kepada petani lain, bukan langsung tampil kedaluwarsa."""
    header = masuk(data_dasar["pengguna"]["wati"].no_hp)
    r = kirim_panen(header, data_dasar["komoditas"]["kubis"].id, 200, TUJUAN_A, besok)
    assert r.status_code == 201, r.text

    slot_id = r.json()["slot_id"]
    detail = client.get(f"/api/slot/{slot_id}", headers=header).json()

    assert detail["cutoff_lewat"] is False
    assert datetime.fromisoformat(detail["cutoff_at"]) > datetime.now(timezone.utc)


def test_muatan_lewat_cutoff_tidak_menerima_kiriman_baru(
    client, data_dasar, masuk, kirim_panen, besok, db
):
    """Petani kedua dengan tujuan searah TIDAK boleh menumpang muatan yang batas
    waktunya sudah lewat — dia harus mendapat muatannya sendiri."""
    header_wati = masuk(data_dasar["pengguna"]["wati"].no_hp)
    r1 = kirim_panen(header_wati, data_dasar["komoditas"]["kubis"].id, 200, TUJUAN_A, besok)
    assert r1.status_code == 201, r1.text
    slot_pertama = r1.json()["slot_id"]

    # Mundurkan cutoff ke masa lalu — meniru muatan yang batas waktunya terlewat.
    slot = db.get(Slot, slot_pertama)
    slot.cutoff_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    db.commit()

    header_dedi = masuk(data_dasar["pengguna"]["dedi"].no_hp)
    r2 = kirim_panen(header_dedi, data_dasar["komoditas"]["kubis"].id, 200, TUJUAN_A, besok)
    assert r2.status_code == 201, r2.text

    assert r2.json()["slot_id"] != slot_pertama
    assert r2.json()["baru_dibuat"] is True

    # Statusnya TETAP DIBUKA: penutupan menetapkan harga final & memesan armada,
    # jadi tidak boleh terjadi diam-diam sebagai efek samping sebuah GET.
    segar = client.get(f"/api/slot/{slot_pertama}", headers=header_wati).json()
    assert segar["status"] == StatusSlot.DIBUKA.value
    assert segar["cutoff_lewat"] is True


def test_pratinjau_dan_kiriman_sepakat_soal_gabung(client, data_dasar, masuk, kirim_panen, besok):
    """Angka yang dijanjikan pratinjau harus angka yang benar-benar didapat.

    Sebelum K14 tujuan calon hilang dari simulasi, sehingga pratinjau bisa
    mengatakan "kamu ikut muatan yang ada" dengan harga rute LAMA sementara
    `buat_kiriman` — yang menghitung belokannya — justru membuka muatan baru.
    """
    header_wati = masuk(data_dasar["pengguna"]["wati"].no_hp)
    assert kirim_panen(header_wati, data_dasar["komoditas"]["kubis"].id, 300, TUJUAN_A, besok).status_code == 201

    header_dedi = masuk(data_dasar["pengguna"]["dedi"].no_hp)
    pratinjau = client.get(
        "/api/kiriman/pratinjau",
        headers=header_dedi,
        params={"volume_kg": 300, "lat": TUJUAN_B[0], "lng": TUJUAN_B[1], "tanggal": str(besok)},
    )
    assert pratinjau.status_code == 200, pratinjau.text
    diramal_ikut = pratinjau.json()["slot_cocok_ada"]

    hasil = kirim_panen(header_dedi, data_dasar["komoditas"]["kubis"].id, 300, TUJUAN_B, besok)
    assert hasil.status_code == 201, hasil.text
    benar_benar_ikut = not hasil.json()["baru_dibuat"]

    assert diramal_ikut == benar_benar_ikut


def test_pratinjau_menghitung_belokan_ke_tujuan_baru(client, data_dasar, masuk, kirim_panen, besok):
    """Kalau pratinjau menyatakan ikut, harga yang dijanjikan harus dihitung dari
    rute SESUDAH belokan — bukan rute muatan lama."""
    header_wati = masuk(data_dasar["pengguna"]["wati"].no_hp)
    assert kirim_panen(header_wati, data_dasar["komoditas"]["kubis"].id, 300, TUJUAN_A, besok).status_code == 201

    header_dedi = masuk(data_dasar["pengguna"]["dedi"].no_hp)
    pratinjau = client.get(
        "/api/kiriman/pratinjau",
        headers=header_dedi,
        params={"volume_kg": 300, "lat": TUJUAN_B[0], "lng": TUJUAN_B[1], "tanggal": str(besok)},
    ).json()

    if not pratinjau["slot_cocok_ada"]:
        pytest.skip("Konfigurasi saat ini memang tidak menggabungkan kedua tujuan ini.")

    hasil = kirim_panen(header_dedi, data_dasar["komoditas"]["kubis"].id, 300, TUJUAN_B, besok)
    detail = client.get(f"/api/slot/{hasil.json()['slot_id']}", headers=header_dedi).json()

    # Harga yang benar-benar berlaku setelah bergabung.
    assert detail["harga_berjalan_per_kg"] == pratinjau["harga_potensial_per_kg"]


def test_aturan_kiriman_terbaca_petani(client, data_dasar, masuk):
    """Petani harus bisa tahu ambangnya SEBELUM menekan Kirim — Panel Asumsi
    hanya boleh dibaca petugas, jadi dulu klien petani buta sama sekali."""
    header = masuk(data_dasar["pengguna"]["wati"].no_hp)
    r = client.get("/api/aturan-kiriman", headers=header)
    assert r.status_code == 200, r.text
    assert r.json()["volume_minimal_kg"] == 50
    assert r.json()["jarak_maks_layanan_km"] > 0
