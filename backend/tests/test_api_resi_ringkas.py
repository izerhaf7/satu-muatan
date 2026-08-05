"""Resi ringkas per lot pada daftar, detail, dan riwayat yang terotorisasi."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from app.models import Lot, Partisipasi, Slot, SlotTujuan
from app.models.enums import StatusPartisipasi, StatusSlot


def test_riwayat_petani_memuat_hanya_resi_lot_miliknya(client, data_dasar, masuk, db):
    titik_kumpul = data_dasar["titik_kumpul"]
    kubis = data_dasar["komoditas"]["kubis"]
    asep = data_dasar["pengguna"]["asep"]
    wati = data_dasar["pengguna"]["wati"]
    slot = Slot(
        kode="SM-RIWAYAT-RESI-01",
        titik_kumpul_id=titik_kumpul.id,
        tanggal_kirim=date.today() + timedelta(days=1),
        cutoff_at=datetime.now(timezone.utc) + timedelta(hours=6),
        status=StatusSlot.TERKUNCI,
        jarak_km=Decimal("80.00"),
        volume_terkunci_kg=600,
        selisih_jaminan_atap=0,
    )
    db.add(slot)
    db.flush()
    db.add(SlotTujuan(slot_id=slot.id, penerima_id=data_dasar["penerima"]["cibiru"].id, urutan=1, jarak_segmen_km=Decimal("80.00")))
    partisipasi_asep = Partisipasi(
        slot_id=slot.id,
        petani_id=asep.id,
        komoditas_id=kubis.id,
        volume_kg=300,
        harga_atap_per_kg=1107,
        status=StatusPartisipasi.TERKUNCI,
    )
    partisipasi_wati = Partisipasi(
        slot_id=slot.id,
        petani_id=wati.id,
        komoditas_id=kubis.id,
        volume_kg=300,
        harga_atap_per_kg=1107,
        status=StatusPartisipasi.TERKUNCI,
    )
    db.add_all([partisipasi_asep, partisipasi_wati])
    db.flush()
    lot_asep = Lot(partisipasi_id=partisipasi_asep.id, kode_qr="LOT-RIWAYAT-ASEP", grade_asal=5)
    db.add_all(
        [
            lot_asep,
            Lot(partisipasi_id=partisipasi_wati.id, kode_qr="LOT-RIWAYAT-WATI", grade_asal=5),
        ]
    )
    db.commit()

    response = client.get("/api/partisipasi/saya", headers=masuk("081200000011"))
    assert response.status_code == 200, response.text
    assert response.json() == [
        {
            "id": str(partisipasi_asep.id),
            "slot_id": str(slot.id),
            "slot_kode": slot.kode,
            "tanggal_kirim": str(slot.tanggal_kirim),
            "nama_komoditas": "Kubis",
            "volume_kg": 300,
            "harga_atap_per_kg": 1107,
            "harga_final_per_kg": None,
            "kembalian_rp": 0,
            "status": "TERKUNCI",
            "resi": [{"lot_id": str(lot_asep.id), "kode_qr": "LOT-RIWAYAT-ASEP"}],
        }
    ]
