"""Test alur login: nomor HP + PIN, masuk cepat demo (K9), profil (§9.1)."""


def test_masuk_berhasil(client, data_dasar):
    r = client.post("/api/auth/masuk", json={"no_hp": "081200000001", "pin": "123456"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["pengguna"]["nama"] == "Bu Nia"
    assert body["pengguna"]["peran"] == "PETUGAS"
    assert body["token"]


def test_masuk_pin_salah(client, data_dasar):
    r = client.post("/api/auth/masuk", json={"no_hp": "081200000001", "pin": "000000"})
    assert r.status_code == 401


def test_masuk_nomor_tidak_terdaftar(client, data_dasar):
    r = client.post("/api/auth/masuk", json={"no_hp": "089999999999", "pin": "123456"})
    assert r.status_code == 401


def test_masuk_demo_semua_akun_k9(client, data_dasar):
    pemetaan = {
        "PETUGAS": ("Bu Nia", "PETUGAS"),
        "PETANI_ASEP": ("Asep", "PETANI"),
        "PETANI_WATI": ("Wati", "PETANI"),
        "PETANI_DEDI": ("Dedi", "PETANI"),
        "PETANI_IJAH": ("Ijah", "PETANI"),
        "PENERIMA_CIBIRU": ("Bu Rina", "PENERIMA"),
    }
    for akun, (nama, peran) in pemetaan.items():
        r = client.post("/api/auth/masuk-demo", json={"akun": akun})
        assert r.status_code == 200, r.text
        assert r.json()["pengguna"]["nama"] == nama
        assert r.json()["pengguna"]["peran"] == peran


def test_masuk_demo_dimatikan_saat_demo_mode_false(client, data_dasar, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("DEMO_MODE", "false")
    get_settings.cache_clear()
    try:
        r = client.post("/api/auth/masuk-demo", json={"akun": "PETUGAS"})
        assert r.status_code == 403
    finally:
        monkeypatch.setenv("DEMO_MODE", "true")
        get_settings.cache_clear()


def test_saya_butuh_token(client, data_dasar):
    r = client.get("/api/auth/saya")
    assert r.status_code == 401


def test_saya_mengembalikan_profil(client, data_dasar, masuk):
    headers = masuk("081200000011")
    r = client.get("/api/auth/saya", headers=headers)
    assert r.status_code == 200
    assert r.json()["nama"] == "Asep"
    assert r.json()["peran"] == "PETANI"
