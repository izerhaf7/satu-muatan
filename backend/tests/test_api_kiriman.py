"""Test endpoint kiriman (spec v2 §3.5) — pencocokan otomatis + pemecahan
kelompok kelebihan muatan di service layer (§3.2 catatan, P4)."""

from datetime import date, timedelta

from app.models import Slot, StatusSlot

BESOK = date.today() + timedelta(days=1)

# Koordinat tujuan: persis di titik penerima Cibiru (di dalam radius koridor).
LAT_CIBIRU, LNG_CIBIRU = -6.9269, 107.7189
# Titik jauh di luar koridor mana pun (~40 km dari penerima terdekat).
LAT_JAUH, LNG_JAUH = -7.2830, 107.5000


def _body(komoditas_id, volume, lat=LAT_CIBIRU, lng=LNG_CIBIRU):
    return {
        "komoditas_id": str(komoditas_id),
        "volume_kg": volume,
        "tanggal_siap": BESOK.isoformat(),
        "lat_tujuan": lat,
        "lng_tujuan": lng,
        "alamat_tujuan": "Cibiru, Bandung",
    }


def test_kiriman_pertama_membuka_muatan_baru(client, data_dasar, masuk):
    kubis = data_dasar["komoditas"]["kubis"]
    r = client.post("/api/kiriman", json=_body(kubis.id, 300), headers=masuk("081200000011"))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["baru_dibuat"] is True
    assert body["harga_atap_per_kg"] > 0
    assert body["jumlah_peserta"] == 1

    # Muatanmu langsung bisa dilihat (Detail Slot tetap layar hasil).
    detail = client.get(f"/api/slot/{body['slot_id']}", headers=masuk("081200000011")).json()
    assert detail["status"] == "DIBUKA"
    assert detail["partisipasi"][0]["harga_atap_per_kg"] == body["harga_atap_per_kg"]


def test_kiriman_kedua_tujuan_dekat_masuk_muatan_sama(client, data_dasar, masuk):
    kubis = data_dasar["komoditas"]["kubis"]
    r1 = client.post("/api/kiriman", json=_body(kubis.id, 300), headers=masuk("081200000011"))
    assert r1.status_code == 201, r1.text

    # Wati: tujuan ~8 km dari tujuan Asep — masih dalam radius koridor 15 km.
    body_wati = _body(kubis.id, 200, lat=-6.9147, lng=107.7000)
    r2 = client.post("/api/kiriman", json=body_wati, headers=masuk("081200000012"))
    assert r2.status_code == 201, r2.text
    assert r2.json()["slot_id"] == r1.json()["slot_id"]
    assert r2.json()["baru_dibuat"] is False
    assert r2.json()["jumlah_peserta"] == 2

    detail = client.get(f"/api/slot/{r1.json()['slot_id']}", headers=masuk("081200000011")).json()
    assert detail["volume_total_kg"] == 500
    # Harga berjalan turun di bawah atap Asep — jaminan atap tetap terkunci.
    assert detail["harga_berjalan_per_kg"] < detail["partisipasi"][0]["harga_atap_per_kg"]


def test_kiriman_di_luar_koridor_ditolak(client, data_dasar, masuk):
    kubis = data_dasar["komoditas"]["kubis"]
    r = client.post("/api/kiriman", json=_body(kubis.id, 100, lat=LAT_JAUH, lng=LNG_JAUH), headers=masuk("081200000011"))
    assert r.status_code == 422


def test_pratinjau_menampilkan_atap_dan_potensi(client, data_dasar, masuk):
    r = client.get(
        "/api/kiriman/pratinjau",
        params={"volume_kg": 300, "lat": LAT_CIBIRU, "lng": LNG_CIBIRU, "tanggal": BESOK.isoformat()},
        headers=masuk("081200000011"),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["harga_atap_per_kg"] > 0
    assert body["harga_potensial_per_kg"] is not None
    # Potensi penghematan selalu di bawah atap (proyeksi 4 petani seukuran).
    assert body["harga_potensial_per_kg"] < body["harga_atap_per_kg"]
    assert body["nama_penerima_terdekat"]


def test_p4_kiriman_kelebihan_kapasitas_membuka_muatan_kedua(client, data_dasar, masuk, db):
    kubis = data_dasar["komoditas"]["kubis"]
    # Kapasitas maksimum armada: maks_kendaraan (4) × FUSO (4.000 kg) = 16.000 kg.
    r1 = client.post("/api/kiriman", json=_body(kubis.id, 9_000), headers=masuk("081200000011"))
    assert r1.status_code == 201, r1.text

    r2 = client.post("/api/kiriman", json=_body(kubis.id, 9_000), headers=masuk("081200000012"))
    assert r2.status_code == 201, r2.text
    # 18.000 kg > 16.000 kg → kiriman kedua memecah ke muatan BARU (§3.2).
    assert r2.json()["slot_id"] != r1.json()["slot_id"]
    assert r2.json()["baru_dibuat"] is True

    # Muatan pertama tetap utuh (yang daftar duluan masuk muatan pertama).
    slot_pertama = db.get(Slot, r1.json()["slot_id"])
    assert slot_pertama.status == StatusSlot.DIBUKA
    assert slot_pertama.volume_terkunci_kg == 9_000
