"""Test endpoint slot (§9.2-9.4): buka slot, gabung, luapan kapasitas, tutup + jaminan atap.

Sebagian test menyeed `slot.jarak_km = 80` langsung ke DB (bukan lewat rute
nearest-neighbor sungguhan) supaya bisa memverifikasi persis terhadap tabel angka
KEPUTUSAN.md K1 (jarak acuan 80 km) — sesuai arahan tugas.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.models import Partisipasi, Slot, SlotTujuan
from app.models.enums import StatusPartisipasi, StatusSlot


def _buat_slot_jarak_80(db, data_dasar, kode="SM-TEST-01"):
    titik_kumpul = data_dasar["titik_kumpul"]
    cibiru = data_dasar["penerima"]["cibiru"]
    slot = Slot(
        kode=kode,
        titik_kumpul_id=titik_kumpul.id,
        tanggal_kirim=date.today() + timedelta(days=1),
        cutoff_at=datetime.now(timezone.utc) + timedelta(hours=6),
        status=StatusSlot.DIBUKA,
        jarak_km=Decimal("80.00"),
        volume_terkunci_kg=0,
        selisih_jaminan_atap=0,
    )
    db.add(slot)
    db.flush()
    db.add(SlotTujuan(slot_id=slot.id, penerima_id=cibiru.id, urutan=1, jarak_segmen_km=Decimal("80.00")))
    db.commit()
    db.refresh(slot)
    return slot


# ---------------------------------------------------------------------------
# Buka slot -> gabung -> bentuk Detail Slot
# ---------------------------------------------------------------------------


def test_buka_slot_gabung_dan_detail_shape(client, data_dasar, masuk):
    header_titik_kumpul = masuk("081200000001")
    cibiru_id = str(data_dasar["penerima"]["cibiru"].id)
    ujungberung_id = str(data_dasar["penerima"]["ujungberung"].id)

    r = client.post(
        "/api/slot",
        headers=header_titik_kumpul,
        json={
            "tanggal_kirim": str(date.today() + timedelta(days=1)),
            "cutoff_at": (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat(),
            "tujuan": [cibiru_id, ujungberung_id],
        },
    )
    assert r.status_code == 201, r.text
    slot = r.json()
    assert slot["status"] == "DIBUKA"
    assert slot["kode"].startswith("SM-")
    assert "CKJ" in slot["kode"]
    assert len(slot["tujuan"]) == 2
    assert {t["urutan"] for t in slot["tujuan"]} == {1, 2}
    assert slot["jarak_km"] > 0
    assert slot["volume_total_kg"] == 0
    assert slot["partisipasi"] == []

    slot_id = slot["id"]

    header_asep = masuk("081200000011")
    kubis_id = str(data_dasar["komoditas"]["kubis"].id)
    r2 = client.post(
        f"/api/slot/{slot_id}/gabung", headers=header_asep, json={"komoditas_id": kubis_id, "volume_kg": 100}
    )
    assert r2.status_code == 201, r2.text
    gabung = r2.json()
    assert gabung["partisipasi"]["nama_petani"] == "Asep"
    assert gabung["partisipasi"]["nama_komoditas"] == "Kubis"
    assert gabung["partisipasi"]["status"] == "TERDAFTAR"
    assert gabung["harga_atap_per_kg"] == gabung["partisipasi"]["harga_atap_per_kg"]

    r3 = client.get(f"/api/slot/{slot_id}", headers=header_asep)
    assert r3.status_code == 200
    detail = r3.json()
    assert detail["volume_total_kg"] == 100
    assert len(detail["partisipasi"]) == 1
    assert detail["atap_saya_per_kg"] == gabung["harga_atap_per_kg"]
    assert detail["hemat_saya_per_kg"] is not None
    assert detail["hemat_saya_per_kg"] >= 0
    assert detail["waktu_server"]
    assert detail["rencana_saat_ini"]["tier"]


def test_gabung_komoditas_tidak_ditemukan(client, data_dasar, masuk, db):
    slot = _buat_slot_jarak_80(db, data_dasar)
    header_asep = masuk("081200000011")
    r = client.post(
        f"/api/slot/{slot.id}/gabung",
        headers=header_asep,
        json={"komoditas_id": "00000000-0000-0000-0000-000000000000", "volume_kg": 10},
    )
    assert r.status_code == 404


def test_gabung_ditolak_kalau_slot_bukan_milik_titik_kumpul_petani(client, data_dasar, masuk, db):
    from app.auth import hash_pin
    from app.models import TitikKumpul, Pengguna
    from app.models.enums import PeranPengguna

    slot = _buat_slot_jarak_80(db, data_dasar)

    titik_kumpul_lain = TitikKumpul(
        nama="Koperasi Lain", kode="LAIN", alamat="Entah", lat=-7.0, lng=107.0
    )
    db.add(titik_kumpul_lain)
    db.flush()
    petani_lain = Pengguna(
        nama="Petani Lain", no_hp="089111111111", pin_hash=hash_pin("123456"),
        peran=PeranPengguna.PETANI, titik_kumpul_id=titik_kumpul_lain.id,
    )
    db.add(petani_lain)
    db.commit()

    header_lain = masuk("089111111111")
    kubis_id = str(data_dasar["komoditas"]["kubis"].id)
    r = client.post(
        f"/api/slot/{slot.id}/gabung", headers=header_lain, json={"komoditas_id": kubis_id, "volume_kg": 10}
    )
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# LUAPAN_KAPASITAS (§5.5, K6)
# ---------------------------------------------------------------------------


def test_gabung_luapan_kapasitas_409(client, data_dasar, masuk, db):
    slot = _buat_slot_jarak_80(db, data_dasar)
    # Slot alternatif: DIBUKA, titik_kumpul & tanggal sama -> harus muncul di slot_alternatif_id.
    slot_alt = _buat_slot_jarak_80(db, data_dasar, kode="SM-TEST-02")
    slot_alt.tanggal_kirim = slot.tanggal_kirim
    db.commit()

    kubis_id = str(data_dasar["komoditas"]["kubis"].id)

    header_asep = masuk("081200000011")
    r1 = client.post(f"/api/slot/{slot.id}/gabung", headers=header_asep, json={"komoditas_id": kubis_id, "volume_kg": 800})
    assert r1.status_code == 201, r1.text
    assert r1.json()["harga_atap_per_kg"] == 415  # K1 T4: 800 kg -> VAN 332.000 -> 415/kg

    header_wati = masuk("081200000012")
    r2 = client.post(f"/api/slot/{slot.id}/gabung", headers=header_wati, json={"komoditas_id": kubis_id, "volume_kg": 10})
    assert r2.status_code == 409, r2.text
    body = r2.json()  # bentuk 409 = LuapanKapasitasOut APA ADANYA (bukan dibungkus {"detail": ...})
    assert body["kode"] == "LUAPAN_KAPASITAS"
    assert body["harga_baru_per_kg"] == 671  # K1 T7: 810 kg -> ENGKEL 543.000 -> ceil(543000/810)=671
    assert body["jumlah_atap_terdampak"] == 1
    assert body["slot_alternatif_id"] == str(slot_alt.id)
    assert body["pesan"]

    # Wati belum tercatat sebagai peserta karena join ditolak.
    r3 = client.get(f"/api/slot/{slot.id}", headers=header_asep)
    assert len(r3.json()["partisipasi"]) == 1


def test_gabung_pratinjau_menunjukkan_luapan_tanpa_membuat_partisipasi(client, data_dasar, masuk, db):
    slot = _buat_slot_jarak_80(db, data_dasar)
    kubis_id = str(data_dasar["komoditas"]["kubis"].id)
    header_asep = masuk("081200000011")
    client.post(f"/api/slot/{slot.id}/gabung", headers=header_asep, json={"komoditas_id": kubis_id, "volume_kg": 800})

    header_wati = masuk("081200000012")
    r = client.post(f"/api/slot/{slot.id}/gabung/pratinjau", headers=header_wati, json={"volume_kg": 10})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["luapan"] is True
    assert body["harga_berjalan_baru_per_kg"] == 671
    assert body["pesan"]

    r2 = client.get(f"/api/slot/{slot.id}", headers=header_asep)
    assert len(r2.json()["partisipasi"]) == 1  # pratinjau tidak membuat partisipasi baru


# ---------------------------------------------------------------------------
# Tutup slot: harga final + jaminan atap (T11, K1)
# ---------------------------------------------------------------------------


def test_tutup_slot_jaminan_atap_t11(client, data_dasar, masuk, db):
    slot = _buat_slot_jarak_80(db, data_dasar)
    kubis = data_dasar["komoditas"]["kubis"]
    asep = data_dasar["pengguna"]["asep"]
    wati = data_dasar["pengguna"]["wati"]

    # T11: A 800 kg atap 415 (bergabung saat slot kosong) + B 10 kg atap 27.100
    # (kalau sendirian butuh MOBIL: 271.000/10). Di-seed langsung ke DB (lihat
    # instruksi tugas) supaya menguji jaminan atap tanpa terhalang gerbang 409.
    partisipasi_a = Partisipasi(
        slot_id=slot.id, petani_id=asep.id, komoditas_id=kubis.id, volume_kg=800, harga_atap_per_kg=415,
        status=StatusPartisipasi.TERDAFTAR,
    )
    partisipasi_b = Partisipasi(
        slot_id=slot.id, petani_id=wati.id, komoditas_id=kubis.id, volume_kg=10, harga_atap_per_kg=27100,
        status=StatusPartisipasi.TERDAFTAR,
    )
    db.add_all([partisipasi_a, partisipasi_b])
    slot.volume_terkunci_kg = 810
    db.commit()

    header_titik_kumpul = masuk("081200000001")
    r = client.post(f"/api/slot/{slot.id}/tutup", headers=header_titik_kumpul)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["status"] == "TERKUNCI"
    assert body["biaya_total"] == 543_000
    assert body["harga_final_per_kg"] == 671
    assert body["selisih_jaminan_atap"] == 204_290

    by_petani = {p["nama_petani"]: p for p in body["partisipasi"]}
    assert by_petani["Asep"]["harga_final_per_kg"] == 415
    assert by_petani["Asep"]["kembalian_rp"] == 0
    assert by_petani["Wati"]["harga_final_per_kg"] == 671
    assert by_petani["Wati"]["kembalian_rp"] == 10 * (27100 - 671)
    assert by_petani["Wati"]["kembalian_rp"] == 264_290

    # Lot + Pengiriman dibuat saat tutup.
    r2 = client.get(f"/api/slot/{slot.id}/lot", headers=header_titik_kumpul)
    assert r2.status_code == 200
    assert len(r2.json()) == 2
    for lot in r2.json():
        assert lot["kode_qr"].startswith(f"LOT-{slot.kode}-")
        assert lot["penerima_id"] is not None

    r3 = client.get(f"/api/slot/{slot.id}/pengiriman", headers=header_titik_kumpul)
    assert r3.status_code == 200, r3.text
    pengiriman = r3.json()
    assert pengiriman["vendor"] == "MOCK"
    assert pengiriman["vendor_ref"].startswith("MOCKV-")
    assert pengiriman["status_vendor"] == "DIPESAN"
    assert pengiriman["timeline"]["dipesan"]


def test_tutup_slot_kosong_ditolak(client, data_dasar, masuk, db):
    slot = _buat_slot_jarak_80(db, data_dasar)
    header_titik_kumpul = masuk("081200000001")
    r = client.post(f"/api/slot/{slot.id}/tutup", headers=header_titik_kumpul)
    assert r.status_code == 422


def test_daftar_slot_ter_scope_per_peran(client, data_dasar, masuk, db):
    _buat_slot_jarak_80(db, data_dasar)

    header_titik_kumpul = masuk("081200000001")
    r_titik_kumpul = client.get("/api/slot", headers=header_titik_kumpul)
    assert len(r_titik_kumpul.json()) == 1

    header_asep = masuk("081200000011")
    r_asep = client.get("/api/slot", headers=header_asep)
    assert len(r_asep.json()) == 1  # petani satu titik_kumpul -> ikut lihat

    header_penerima = masuk("081200000021")
    r_penerima = client.get("/api/slot", headers=header_penerima)
    assert len(r_penerima.json()) == 1  # Cibiru adalah tujuan slot ini
