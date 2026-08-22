"""Uji lokasi petugas dan penyaringan papan tugas berbasis radius."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.models import Slot, TitikKumpul
from app.models.enums import StatusSlot


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
