"""Uji lokasi petugas dan penyaringan papan tugas berbasis radius."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.models import Slot, TitikKumpul
from app.models.enums import StatusPartisipasi, StatusSlot


def _slot(db, titik_kumpul, kode):
    slot = Slot(
        kode=kode,
        titik_kumpul_id=titik_kumpul.id,
        petugas_id=None,
        tanggal_kirim=date.today() + timedelta(days=1),
        cutoff_at=datetime.now(timezone.utc) + timedelta(hours=6),
        status=StatusSlot.DIBUKA,
        jarak_km=Decimal("10.00"),
        volume_terkunci_kg=0,
        selisih_jaminan_atap=0,
    )
    db.add(slot)
    db.commit()
    return slot


def test_lokasi_petugas_tersimpan(client, data_dasar, masuk, db):
    header = masuk("081200000001")

    response = client.post("/api/pengguna/lokasi", headers=header, json={"lat": -7.36, "lng": 107.79})

    assert response.status_code == 200, response.text
    assert response.json()["lat"] == -7.36
    assert response.json()["lng"] == 107.79
    pengguna = data_dasar["pengguna"]["titik_kumpul"]
    db.refresh(pengguna)
    assert pengguna.terkini_lat == -7.36
    assert pengguna.terkini_lng == 107.79
    assert pengguna.lokasi_diperbarui_pada is not None


def test_papan_tugas_hanya_menampilkan_slot_dalam_radius(client, data_dasar, masuk, db):
    titik_asal = data_dasar["titik_kumpul"]
    titik_dekat = TitikKumpul(nama="Titik dekat", kode="DEKAT", alamat="Dekat", lat=-7.3661, lng=107.8961)
    titik_jauh = TitikKumpul(nama="Titik jauh", kode="JAUH", alamat="Jauh", lat=-7.3661, lng=108.1961)
    db.add_all([titik_dekat, titik_jauh])
    db.flush()
    dekat = _slot(db, titik_dekat, "SM-DEKAT")
    jauh = _slot(db, titik_jauh, "SM-JAUH")

    header = masuk("081200000001")
    lokasi = client.post("/api/pengguna/lokasi", headers=header, json={"lat": titik_asal.lat, "lng": titik_asal.lng})
    assert lokasi.status_code == 200, lokasi.text

    response = client.get("/api/slot/tersedia", headers=header)

    assert response.status_code == 200, response.text
    hasil = {item["id"]: item for item in response.json()}
    assert str(dekat.id) in hasil
    assert str(jauh.id) not in hasil
    assert hasil[str(dekat.id)]["jarak_dari_driver_km"] > 0


def test_papan_tugas_kosong_sebelum_lokasi_diberikan(client, data_dasar, masuk, db):
    _slot(db, data_dasar["titik_kumpul"], "SM-TANPA-LOKASI")

    response = client.get("/api/slot/tersedia", headers=masuk("081200000001"))

    assert response.status_code == 200, response.text
    assert response.json() == []


def test_papan_tugas_mengukur_ke_titik_terdekat_termasuk_jemput(client, data_dasar, masuk, db):
    """K14: rute dua tahap — jarak papan tugas diukur ke titik TERDEKAT muatan
    (titik kumpul, jemput, atau tujuan). Titik kumpul jauh tapi jemput dekat
    tetap menampilkan muatan, karena petugas menjemput di lokasi petani."""
    from app.models import Partisipasi, SlotJemput

    titik_jauh = TitikKumpul(nama="Titik jauh", kode="JAUHQ", alamat="Jauh", lat=-7.3661, lng=108.1961)
    db.add(titik_jauh)
    db.flush()
    slot = Slot(
        kode="SM-JEMPUT-DEKAT",
        titik_kumpul_id=titik_jauh.id,
        petugas_id=None,
        tanggal_kirim=date.today() + timedelta(days=1),
        cutoff_at=datetime.now(timezone.utc) + timedelta(hours=6),
        status=StatusSlot.DIBUKA,
        jarak_km=Decimal("10.00"),
        volume_terkunci_kg=0,
        selisih_jaminan_atap=0,
    )
    db.add(slot)
    db.flush()
    partisipasi = Partisipasi(
        slot_id=slot.id,
        petani_id=data_dasar["pengguna"]["wati"].id,
        komoditas_id=data_dasar["komoditas"]["kubis"].id,
        volume_kg=100,
        harga_atap_per_kg=1000,
        kembalian_rp=0,
        status=StatusPartisipasi.TERDAFTAR,
    )
    db.add(partisipasi)
    db.flush()
    db.add(
        SlotJemput(
            slot_id=slot.id,
            partisipasi_id=partisipasi.id,
            urutan=1,
            lat=-7.3661,
            lng=107.8961,
            alamat="Dekat driver",
            jarak_segmen_km=Decimal("10.00"),
        )
    )
    db.commit()

    # Driver di titik_asal: jemput ~10 km (harus tampil), titik kumpul ~37 km
    # (harus tidak menyaring berdasarkan itu saja).
    header = masuk("081200000001")
    lokasi = client.post(
        "/api/pengguna/lokasi", headers=header, json={"lat": data_dasar["titik_kumpul"].lat, "lng": data_dasar["titik_kumpul"].lng}
    )
    assert lokasi.status_code == 200, lokasi.text

    response = client.get("/api/slot/tersedia", headers=header)

    assert response.status_code == 200, response.text
    hasil = {item["id"]: item for item in response.json()}
    assert str(slot.id) in hasil
    assert hasil[str(slot.id)]["jarak_dari_driver_km"] < 12
