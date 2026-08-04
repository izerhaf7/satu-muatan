"""Regresi K14 — rute penjemputan & foto muat wajib.

Dua hal yang sebelumnya tidak ada sama sekali:

1. **Lokasi penjemputan.** Semua petani dianggap berangkat dari satu titik
   kumpul, jadi petugas tidak punya alamat untuk dituju dan `jarak_km` (dasar
   harga) tidak menghitung leg penjemputan.
2. **Foto muat wajib.** Kolom & UI-nya sudah ada sejak lama, tapi tidak ada satu
   pun yang menegakkannya — muatan bisa berangkat tanpa satu foto pun, dan
   atribusi mutu jadi klaim tanpa sandaran.
"""

from datetime import date, timedelta

from app.models import Slot, SlotJemput

BESOK = date.today() + timedelta(days=1)
TUJUAN = (-6.9269, 107.7189)
# Dua kebun berjauhan dari titik kumpul Cikajang (-7.3661, 107.7961).
KEBUN_A = (-7.3400, 107.7700)
KEBUN_B = (-7.2000, 107.7500)

FOTO = "ZmFrZS1mb3RvLW11YXQ="


def _kirim(client, header, komoditas_id, volume, tujuan, asal=None, alamat_asal=None):
    body = {
        "komoditas_id": str(komoditas_id),
        "volume_kg": volume,
        "tanggal_siap": str(BESOK),
        "lat_tujuan": tujuan[0],
        "lng_tujuan": tujuan[1],
        "alamat_tujuan": "Pasar Kordon, Bandung",
    }
    if asal is not None:
        body["lat_asal"] = asal[0]
        body["lng_asal"] = asal[1]
        body["rincian_asal"] = {"alamat": alamat_asal or "Kebun", "desa": "Mekarjaya", "kecamatan": "Cikajang"}
    r = client.post("/api/kiriman", json=body, headers=header)
    assert r.status_code == 201, r.text
    return r.json()


def test_penjemputan_masuk_rute_dan_menambah_jarak(client, data_dasar, masuk, db):
    """Rute = titik kumpul → semua lokasi jemput → semua tujuan.

    Diukur pada muatan yang SAMA: petani pertama tanpa titik jemput, lalu petani
    kedua dengan titik jemput ke tujuan yang sama. Jarak muatan harus bertambah
    karena truk kini harus memutar menjemput panennya."""
    kubis = data_dasar["komoditas"]["kubis"]

    pertama = _kirim(client, masuk("081200000011"), kubis.id, 300, TUJUAN)
    jarak_tanpa = float(db.get(Slot, pertama["slot_id"]).jarak_km)
    assert db.query(SlotJemput).filter_by(slot_id=pertama["slot_id"]).count() == 0

    kedua = _kirim(
        client, masuk("081200000012"), kubis.id, 300, TUJUAN, asal=KEBUN_A, alamat_asal="Kebun Wati, Cikajang"
    )
    assert kedua["slot_id"] == pertama["slot_id"], "keduanya searah, seharusnya satu muatan"

    db.expire_all()
    slot = db.get(Slot, kedua["slot_id"])
    jemput = db.query(SlotJemput).filter_by(slot_id=slot.id).all()

    assert len(jemput) == 1
    assert jemput[0].alamat == "Kebun Wati, Cikajang"
    # Leg penjemputan benar-benar menambah rute, bukan sekadar dicatat.
    assert float(slot.jarak_km) > jarak_tanpa


def test_dua_petani_menghasilkan_dua_perhentian_jemput_berurutan(client, data_dasar, masuk, db):
    kubis = data_dasar["komoditas"]["kubis"]
    a = _kirim(client, masuk("081200000011"), kubis.id, 300, TUJUAN, asal=KEBUN_A, alamat_asal="Kebun A")
    b = _kirim(client, masuk("081200000012"), kubis.id, 300, TUJUAN, asal=KEBUN_B, alamat_asal="Kebun B")
    assert a["slot_id"] == b["slot_id"], "kedua petani seharusnya satu muatan"

    slot = db.get(Slot, a["slot_id"])
    jemput = db.query(SlotJemput).filter_by(slot_id=slot.id).order_by(SlotJemput.urutan).all()

    assert [j.urutan for j in jemput] == [1, 2]
    assert {j.alamat for j in jemput} == {"Kebun A", "Kebun B"}
    # Nearest-neighbor dari Cikajang: Kebun A (lebih dekat) lebih dulu.
    assert jemput[0].alamat == "Kebun A"

    # Invarian: jarak muatan = jumlah SELURUH segmen, jemput + antar.
    total_segmen = sum(float(j.jarak_segmen_km) for j in jemput) + sum(
        float(t.jarak_segmen_km) for t in slot.tujuan
    )
    assert abs(float(slot.jarak_km) - total_segmen) < 0.05


def test_kiriman_tanpa_koordinat_asal_tetap_jalan(client, data_dasar, masuk, db):
    """Kompatibilitas mundur — alur ringkas tanpa titik jemput tidak boleh pecah."""
    kubis = data_dasar["komoditas"]["kubis"]
    hasil = _kirim(client, masuk("081200000011"), kubis.id, 300, TUJUAN)
    slot = db.get(Slot, hasil["slot_id"])
    assert db.query(SlotJemput).filter_by(slot_id=slot.id).count() == 0
    assert float(slot.jarak_km) > 0


# ---------------------------------------------------------------------------
# Foto muat wajib
# ---------------------------------------------------------------------------


def _siapkan_muat(client, data_dasar, masuk, ambil_tugas):
    kubis = data_dasar["komoditas"]["kubis"]
    hasil = _kirim(client, masuk("081200000011"), kubis.id, 300, TUJUAN, asal=KEBUN_A, alamat_asal="Kebun A")
    header = masuk("081200000001")
    ambil_tugas(header, hasil["slot_id"])
    r = client.post(f"/api/slot/{hasil['slot_id']}/tutup", headers=header)
    assert r.status_code == 200, r.text
    lots = client.get(f"/api/slot/{hasil['slot_id']}/lot", headers=header).json()
    return header, hasil["slot_id"], lots


def test_muat_tanpa_foto_ditolak(client, data_dasar, masuk, ambil_tugas):
    header, _, lots = _siapkan_muat(client, data_dasar, masuk, ambil_tugas)
    r = client.patch(
        f"/api/lot/{lots[0]['id']}/muat",
        headers=header,
        json={"berat_aktual_kg": 300, "grade_asal": 5},
    )
    assert r.status_code == 422, r.text
    assert "foto muat wajib" in r.json()["detail"].lower()


def test_selesai_muat_menyebut_lot_yang_belum_berfoto(client, data_dasar, masuk, ambil_tugas, db):
    """Petugas sedang berdiri di truk — dia butuh tahu lot MANA yang kurang."""
    from app.models import Lot

    header, slot_id, lots = _siapkan_muat(client, data_dasar, masuk, ambil_tugas)
    r = client.patch(
        f"/api/lot/{lots[0]['id']}/muat",
        headers=header,
        json={"berat_aktual_kg": 300, "foto_muat_base64": FOTO, "grade_asal": 5},
    )
    assert r.status_code == 200, r.text

    # Hapus fotonya diam-diam, meniru data yang lolos dari jalur lain.
    lot = db.get(Lot, lots[0]["id"])
    lot.foto_muat = None
    db.commit()

    r = client.post(f"/api/slot/{slot_id}/selesai-muat", headers=header)
    assert r.status_code == 422, r.text
    assert "Wati" in r.json()["detail"] or "foto muat" in r.json()["detail"].lower()


def test_muat_dengan_foto_lolos_sampai_berangkat(client, data_dasar, masuk, ambil_tugas):
    header, slot_id, lots = _siapkan_muat(client, data_dasar, masuk, ambil_tugas)
    for lot in lots:
        r = client.patch(
            f"/api/lot/{lot['id']}/muat",
            headers=header,
            json={"berat_aktual_kg": 300, "foto_muat_base64": FOTO, "grade_asal": 5},
        )
        assert r.status_code == 200, r.text
        assert r.json()["foto_muat"] == FOTO

    r = client.post(f"/api/slot/{slot_id}/selesai-muat", headers=header)
    assert r.status_code == 200, r.text
