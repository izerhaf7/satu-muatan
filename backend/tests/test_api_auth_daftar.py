"""Pendaftaran akun mandiri — Petani & Penerima (self-service, tanpa OTP).

PETUGAS sengaja TIDAK bisa daftar lewat sini (peran paling sensitif: bisa
ambil tugas & tandai mutu). Ditegakkan server lewat `Literal["PETANI",
"PENERIMA"]` di `DaftarRequest`, bukan cuma disembunyikan di UI.
"""

from datetime import date, timedelta

CIBIRU = (-6.9269, 107.7189)
BESOK = date.today() + timedelta(days=1)


def test_daftar_petani_sukses(client, data_dasar):
    r = client.post(
        "/api/auth/daftar",
        json={"nama": "Petani Baru", "no_hp": "081299900001", "pin": "111111", "peran": "PETANI"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["token"]
    assert body["pengguna"]["nama"] == "Petani Baru"
    assert body["pengguna"]["peran"] == "PETANI"
    assert body["pengguna"]["titik_kumpul_id"] == str(data_dasar["titik_kumpul"].id)
    assert body["pengguna"]["penerima_id"] is None


def test_daftar_penerima_sukses(client, data_dasar):
    r = client.post(
        "/api/auth/daftar",
        json={"nama": "Dapur Baru", "no_hp": "081299900002", "pin": "111111", "peran": "PENERIMA"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["pengguna"]["peran"] == "PENERIMA"
    assert body["pengguna"]["titik_kumpul_id"] is None
    assert body["pengguna"]["penerima_id"] is None


def test_daftar_token_bisa_langsung_dipakai(client, data_dasar):
    r = client.post(
        "/api/auth/daftar",
        json={"nama": "Petani Baru", "no_hp": "081299900003", "pin": "111111", "peran": "PETANI"},
    )
    token = r.json()["token"]
    r2 = client.get("/api/auth/saya", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["nama"] == "Petani Baru"


def test_daftar_nomor_hp_dobel(client, data_dasar):
    r1 = client.post(
        "/api/auth/daftar",
        json={"nama": "Pertama", "no_hp": "081299900004", "pin": "111111", "peran": "PETANI"},
    )
    assert r1.status_code == 201, r1.text
    r2 = client.post(
        "/api/auth/daftar",
        json={"nama": "Kedua", "no_hp": "081299900004", "pin": "222222", "peran": "PETANI"},
    )
    assert r2.status_code == 409


def test_daftar_nomor_hp_sudah_dipakai_akun_lama(client, data_dasar):
    r = client.post(
        "/api/auth/daftar",
        json={"nama": "Duplikat Asep", "no_hp": "081200000011", "pin": "111111", "peran": "PETANI"},
    )
    assert r.status_code == 409


def test_daftar_peran_petugas_ditolak(client, data_dasar):
    r = client.post(
        "/api/auth/daftar",
        json={"nama": "Coba Jadi Petugas", "no_hp": "081299900005", "pin": "111111", "peran": "PETUGAS"},
    )
    assert r.status_code == 422


def test_daftar_pin_kurang_digit(client, data_dasar):
    r = client.post(
        "/api/auth/daftar",
        json={"nama": "Petani Baru", "no_hp": "081299900006", "pin": "1234", "peran": "PETANI"},
    )
    assert r.status_code == 422


def test_daftar_no_hp_alfabet_ditolak(client, data_dasar):
    r = client.post(
        "/api/auth/daftar",
        json={"nama": "Petani Baru", "no_hp": "abc12345678", "pin": "111111", "peran": "PETANI"},
    )
    assert r.status_code == 422


def test_daftar_no_hp_tidak_diawali_nol_ditolak(client, data_dasar):
    r = client.post(
        "/api/auth/daftar",
        json={"nama": "Petani Baru", "no_hp": "81234567890", "pin": "111111", "peran": "PETANI"},
    )
    assert r.status_code == 422


def test_daftar_no_hp_terlalu_pendek_ditolak(client, data_dasar):
    r = client.post(
        "/api/auth/daftar",
        json={"nama": "Petani Baru", "no_hp": "0812345", "pin": "111111", "peran": "PETANI"},
    )
    assert r.status_code == 422


def test_daftar_nama_kosong(client, data_dasar):
    r = client.post(
        "/api/auth/daftar",
        json={"nama": "   ", "no_hp": "081299900007", "pin": "111111", "peran": "PETANI"},
    )
    assert r.status_code == 422


def test_daftar_petani_bisa_langsung_kirim_panen(client, data_dasar, kirim_panen):
    r = client.post(
        "/api/auth/daftar",
        json={"nama": "Petani Baru", "no_hp": "081299900008", "pin": "111111", "peran": "PETANI"},
    )
    assert r.status_code == 201, r.text
    token = r.json()["token"]
    header = {"Authorization": f"Bearer {token}"}
    kubis = data_dasar["komoditas"]["kubis"]

    hasil = kirim_panen(header, kubis.id, 300, CIBIRU, BESOK)
    assert hasil.status_code == 201, hasil.text


def test_daftar_penerima_bisa_lihat_lot_lewat_resi(client, data_dasar, masuk, kirim_panen):
    kubis = data_dasar["komoditas"]["kubis"]
    r1 = kirim_panen(masuk("081200000011"), kubis.id, 300, CIBIRU, BESOK)
    assert r1.status_code == 201, r1.text
    slot_id = r1.json()["slot_id"]
    r_berangkat = client.post(f"/api/demo/muatan/{slot_id}/berangkatkan", headers=masuk("081200000001"))
    assert r_berangkat.status_code == 200, r_berangkat.text
    resi = r_berangkat.json()["resi"][0]

    r_daftar = client.post(
        "/api/auth/daftar",
        json={"nama": "Dapur Baru", "no_hp": "081299900009", "pin": "111111", "peran": "PENERIMA"},
    )
    assert r_daftar.status_code == 201, r_daftar.text
    token = r_daftar.json()["token"]

    r_bukti = client.get(f"/api/lot/qr/{resi}", headers={"Authorization": f"Bearer {token}"})
    assert r_bukti.status_code == 200, r_bukti.text


def test_daftar_penerima_tidak_lihat_daftar_lot_akun_lain(client, data_dasar, masuk, kirim_panen):
    """Regresi: akun Penerima yang daftar sendiri (penerima_id kosong) TIDAK
    boleh melihat daftar "lot masuk" — itu punya orang lain sepenuhnya, tidak
    ada hubungan apa pun dengan akun baru ini. Hanya resi yang membuktikan hak
    lihat (lihat test di atas), bukan sekadar berstatus PENERIMA."""
    kubis = data_dasar["komoditas"]["kubis"]
    r1 = kirim_panen(masuk("081200000011"), kubis.id, 300, CIBIRU, BESOK)
    assert r1.status_code == 201, r1.text
    slot_id = r1.json()["slot_id"]
    r_berangkat = client.post(f"/api/demo/muatan/{slot_id}/berangkatkan", headers=masuk("081200000001"))
    assert r_berangkat.status_code == 200, r_berangkat.text

    r_daftar = client.post(
        "/api/auth/daftar",
        json={"nama": "Penerima Asing", "no_hp": "081299900010", "pin": "111111", "peran": "PENERIMA"},
    )
    assert r_daftar.status_code == 201, r_daftar.text
    token = r_daftar.json()["token"]

    r_masuk = client.get("/api/lot/masuk", headers={"Authorization": f"Bearer {token}"})
    assert r_masuk.status_code == 200, r_masuk.text
    assert r_masuk.json() == []
