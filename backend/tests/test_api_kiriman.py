"""Test endpoint kiriman (spec v2 §3.5) — pencocokan otomatis + pemecahan
kelompok kelebihan muatan di service layer (§3.2 catatan, P4)."""

from datetime import date, timedelta

from app.models import Lot, Partisipasi, Slot, StatusSlot

BESOK = date.today() + timedelta(days=1)

# Koordinat tujuan: persis di titik penerima Cibiru (di dalam radius koridor).
LAT_CIBIRU, LNG_CIBIRU = -6.9269, 107.7189
# Titik SANGAT jauh — di luar `jarak_maks_layanan_km` (200 km) dari titik kumpul
# Cikajang. K13: tujuan bebas, tapi tetap ada batas kewajaran.
LAT_JAUH, LNG_JAUH = -6.1754, 106.8272  # Jakarta, ±270 km rute dari Cikajang


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


def test_tujuan_di_luar_jangkauan_layanan_ditolak(client, data_dasar, masuk):
    """K13: tujuan bebas, tapi di luar `jarak_maks_layanan_km` tetap ditolak."""
    kubis = data_dasar["komoditas"]["kubis"]
    r = client.post("/api/kiriman", json=_body(kubis.id, 100, lat=LAT_JAUH, lng=LNG_JAUH), headers=masuk("081200000011"))
    assert r.status_code == 422
    assert "terlalu jauh" in r.json()["detail"].lower()


def test_tujuan_bebas_membuat_alamat_baru(client, data_dasar, masuk, db):
    """K13 inti: petani menaruh titik tujuan yang belum pernah ada di sistem —
    diterima, dan alamatnya tercatat otomatis."""
    from app.models import Penerima

    kubis = data_dasar["komoditas"]["kubis"]
    sebelum = db.query(Penerima).count()
    # Titik acak di Bandung selatan, jauh dari tiga alamat seed tapi masih terlayani.
    r = client.post(
        "/api/kiriman",
        json=_body(kubis.id, 300, lat=-6.9800, lng=107.6200) | {"alamat_tujuan": "Warung Bu Imas, Dayeuhkolot"},
        headers=masuk("081200000011"),
    )
    assert r.status_code == 201, r.text
    assert db.query(Penerima).count() == sebelum + 1
    baru = db.query(Penerima).filter_by(dibuat_otomatis=True).one()
    assert baru.alamat == "Warung Bu Imas, Dayeuhkolot"


def test_volume_di_bawah_minimal_ditolak(client, data_dasar, masuk):
    """K13: kiriman receh bisa menggeser rencana armada seluruh muatan."""
    kubis = data_dasar["komoditas"]["kubis"]
    r = client.post("/api/kiriman", json=_body(kubis.id, 10), headers=masuk("081200000011"))
    assert r.status_code == 422
    assert "minimal" in r.json()["detail"].lower()


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
    assert body["jarak_ke_penerima_km"] > 0


def test_tujuan_peserta_kedua_masuk_rute_dan_jarak_dihitung_ulang(client, data_dasar, masuk, db):
    """REGRESI CACAT #1 (K13). Dulu kiriman yang bergabung tidak pernah menambah
    `SlotTujuan`: barangnya ikut truk tapi rutenya tidak pernah lewat alamatnya,
    dan `jarak_km` tidak dihitung ulang. Sekarang tujuan itu wajib masuk rute."""
    from app.models import SlotTujuan

    kubis = data_dasar["komoditas"]["kubis"]
    r1 = client.post("/api/kiriman", json=_body(kubis.id, 300), headers=masuk("081200000011"))
    assert r1.status_code == 201, r1.text
    slot_id = r1.json()["slot_id"]
    jarak_awal = client.get(f"/api/slot/{slot_id}", headers=masuk("081200000011")).json()["jarak_km"]

    # Wati: tujuan berbeda (±8 km) tapi masih satu koridor.
    r2 = client.post(
        "/api/kiriman",
        json=_body(kubis.id, 200, lat=-6.9147, lng=107.7000) | {"alamat_tujuan": "Ujungberung"},
        headers=masuk("081200000012"),
    )
    assert r2.status_code == 201, r2.text
    assert r2.json()["slot_id"] == slot_id

    tujuan = db.query(SlotTujuan).filter_by(slot_id=slot_id).all()
    assert len(tujuan) == 2, "tujuan petani kedua wajib masuk rute muatan"
    assert sorted(t.urutan for t in tujuan) == [1, 2]

    detail = client.get(f"/api/slot/{slot_id}", headers=masuk("081200000011")).json()
    assert detail["jarak_km"] > jarak_awal, "rute bertambah, jarak wajib dihitung ulang"
    assert len(detail["tujuan"]) == 2
    assert all("lat" in t and "lng" in t for t in detail["tujuan"])


def test_kiriman_yang_menaikkan_harga_grup_membuka_muatan_baru(client, data_dasar, masuk, db):
    """REGRESI CACAT #2 (K13). Biaya armada adalah fungsi tangga: melewati batas
    kapasitas tier menaikkan harga per kg SEMUA peserta (mis. 800 → 801 kg naik
    ±72%). Kiriman seperti itu harus membuka muatan sendiri, bukan ditolak 409
    atau diam-diam merugikan peserta lama."""
    kubis = data_dasar["komoditas"]["kubis"]
    # 800 kg pas kapasitas VAN — tier paling efisien di titik ini.
    r1 = client.post("/api/kiriman", json=_body(kubis.id, 800), headers=masuk("081200000011"))
    assert r1.status_code == 201, r1.text
    slot_id = r1.json()["slot_id"]
    harga_sebelum = client.get(f"/api/slot/{slot_id}", headers=masuk("081200000011")).json()["harga_berjalan_per_kg"]

    # Tambahan kecil ini akan memaksa naik tier kalau digabungkan.
    r2 = client.post("/api/kiriman", json=_body(kubis.id, 60), headers=masuk("081200000012"))
    assert r2.status_code == 201, r2.text
    assert r2.json()["slot_id"] != slot_id, "seharusnya membuka muatan baru, bukan menumpang"
    assert r2.json()["baru_dibuat"] is True

    # Peserta lama tidak terganggu sama sekali.
    sesudah = client.get(f"/api/slot/{slot_id}", headers=masuk("081200000011")).json()
    assert sesudah["harga_berjalan_per_kg"] == harga_sebelum
    assert sesudah["volume_total_kg"] == 800


def test_muatan_lahir_tanpa_driver_lalu_muncul_di_papan_tugas(client, data_dasar, masuk, db):
    """K14 (menimpa K13): driver TIDAK lagi ditugaskan otomatis.

    K13 menempelkan petugas pada muatan begitu ia lahir, tanpa batas apa pun —
    satu petugas aktif menyerap seluruh muatan di sistem dan tidak ada endpoint
    yang bisa mengubahnya. Sekarang muatan menunggu di papan tugas."""
    from app.models import Slot

    kubis = data_dasar["komoditas"]["kubis"]
    r = client.post("/api/kiriman", json=_body(kubis.id, 300), headers=masuk("081200000011"))
    assert r.status_code == 201, r.text
    slot_id = r.json()["slot_id"]

    slot = db.get(Slot, slot_id)
    assert slot.petugas_id is None
    partisipasi = db.query(Partisipasi).filter_by(slot_id=slot_id).one()
    db.add(Lot(partisipasi_id=partisipasi.id, kode_qr="LOT-TERSedia-TIDAK-BOCOR", grade_asal=5))
    db.commit()

    header_petugas = masuk("081200000001")
    tersedia = client.get("/api/slot/tersedia", headers=header_petugas)
    assert tersedia.status_code == 200, tersedia.text
    assert slot_id in [s["id"] for s in tersedia.json()]
    assert all(s["resi"] == [] for s in tersedia.json())

    diterima = client.post(f"/api/slot/{slot_id}/terima", headers=header_petugas)
    assert diterima.status_code == 200, diterima.text
    assert diterima.json()["resi"] == [{"lot_id": str(db.query(Lot).filter_by(partisipasi_id=partisipasi.id).one().id), "kode_qr": "LOT-TERSedia-TIDAK-BOCOR"}]


def test_petugas_hanya_boleh_membawa_satu_muatan_aktif(client, data_dasar, masuk, db):
    """K14: sopir tidak bisa membawa dua truk sekaligus."""
    kubis = data_dasar["komoditas"]["kubis"]
    # Dua muatan terpisah: volume besar memaksa kiriman kedua memecah sendiri.
    r1 = client.post("/api/kiriman", json=_body(kubis.id, 9_000), headers=masuk("081200000011"))
    r2 = client.post("/api/kiriman", json=_body(kubis.id, 9_000), headers=masuk("081200000012"))
    assert r1.json()["slot_id"] != r2.json()["slot_id"]

    header_petugas = masuk("081200000001")
    pertama = client.post(f"/api/slot/{r1.json()['slot_id']}/terima", headers=header_petugas)
    assert pertama.status_code == 200, pertama.text

    kedua = client.post(f"/api/slot/{r2.json()['slot_id']}/terima", headers=header_petugas)
    assert kedua.status_code == 409, kedua.text
    assert "batas" in kedua.json()["detail"].lower()

    # Mengambil ulang muatan yang SAMA tetap boleh — idempoten, bukan galat.
    lagi = client.post(f"/api/slot/{r1.json()['slot_id']}/terima", headers=header_petugas)
    assert lagi.status_code == 200, lagi.text


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
