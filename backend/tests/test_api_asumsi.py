"""Test Panel Asumsi (§9.9): mengubah konfigurasi langsung mempengaruhi pratinjau harga."""


def test_konfigurasi_patch_mempengaruhi_pratinjau(client, data_dasar, masuk):
    headers = masuk("081200000001")
    cibiru_id = str(data_dasar["penerima"]["cibiru"].id)

    r1 = client.post(
        "/api/slot/pratinjau", headers=headers, json={"tujuan": [cibiru_id], "skenario_volume": [800]}
    )
    assert r1.status_code == 200, r1.text
    jarak_awal = r1.json()["jarak_km"]
    harga_awal = r1.json()["tabel_harga"][0]["harga_per_kg"]

    r2 = client.patch("/api/konfigurasi/faktor_jalan", headers=headers, json={"nilai": "2.0"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["nilai"] == "2.0"

    r3 = client.post(
        "/api/slot/pratinjau", headers=headers, json={"tujuan": [cibiru_id], "skenario_volume": [800]}
    )
    assert r3.status_code == 200, r3.text
    jarak_baru = r3.json()["jarak_km"]
    harga_baru = r3.json()["tabel_harga"][0]["harga_per_kg"]

    # faktor_jalan naik dari 1.30 -> 2.0: jarak & harga wajib ikut naik (bukti bahwa
    # tidak ada angka bisnis hardcoded — semua dari tabel konfigurasi, CLAUDE.md #1).
    assert jarak_baru > jarak_awal
    assert harga_baru > harga_awal


def test_konfigurasi_patch_menolak_nilai_tidak_sesuai_tipe(client, data_dasar, masuk):
    headers = masuk("081200000001")
    r = client.patch("/api/konfigurasi/kecepatan_rata_kmh", headers=headers, json={"nilai": "bukan-angka"})
    assert r.status_code == 422


def test_konfigurasi_patch_kunci_tidak_ada(client, data_dasar, masuk):
    headers = masuk("081200000001")
    r = client.patch("/api/konfigurasi/tidak-ada-kunci-begini", headers=headers, json={"nilai": "1"})
    assert r.status_code == 404


def test_konfigurasi_hanya_koperasi(client, data_dasar, masuk):
    headers = masuk("081200000011")  # Asep, PETANI
    r = client.get("/api/konfigurasi", headers=headers)
    assert r.status_code == 403


def test_tier_kendaraan_get_dan_patch(client, data_dasar, masuk):
    headers = masuk("081200000001")
    r = client.get("/api/tier-kendaraan", headers=headers)
    assert r.status_code == 200
    van = next(t for t in r.json() if t["kode"] == "VAN")

    r2 = client.patch(f"/api/tier-kendaraan/{van['id']}", headers=headers, json={"tarif_dasar": 100000})
    assert r2.status_code == 200, r2.text
    assert r2.json()["tarif_dasar"] == 100000
    assert r2.json()["tarif_per_km"] == van["tarif_per_km"]  # field lain tidak berubah
