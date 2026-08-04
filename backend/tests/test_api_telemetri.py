"""Test endpoint telemetri (spec v2 §5.3) — lazy-generate, deterministik, ringkasan Q10."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models import Partisipasi, Pengiriman, Slot, SlotTujuan, StatusPartisipasi, StatusSlot


def _slot_jalan(db, data_dasar):
    tk = data_dasar["titik_kumpul"]
    cibiru = data_dasar["penerima"]["cibiru"]
    kubis = data_dasar["komoditas"]["kubis"]
    asep = data_dasar["pengguna"]["asep"]

    berangkat = datetime.now(timezone.utc) - timedelta(hours=2)
    slot = Slot(
        kode="SM-TELEM-01",
        titik_kumpul_id=tk.id,
        tanggal_kirim=berangkat.date(),
        cutoff_at=berangkat - timedelta(hours=1),
        status=StatusSlot.JALAN,
        jarak_km=Decimal("70.0"),
        volume_terkunci_kg=300,
    )
    db.add(slot)
    db.flush()
    db.add(SlotTujuan(slot_id=slot.id, penerima_id=cibiru.id, urutan=1, jarak_segmen_km=Decimal("70.0")))
    db.add(
        Partisipasi(
            slot_id=slot.id,
            petani_id=asep.id,
            komoditas_id=kubis.id,
            volume_kg=300,
            harga_atap_per_kg=1000,
            status=StatusPartisipasi.DIMUAT,
        )
    )
    db.add(
        Pengiriman(
            slot_id=slot.id,
            vendor="MOCK",
            status_vendor="JALAN",
            waktu_berangkat=berangkat,
        )
    )
    db.commit()
    return slot


def test_telemetri_bangkit_dan_deterministik(client, db, data_dasar, masuk):
    slot = _slot_jalan(db, data_dasar)
    headers = masuk("081200000011")

    r1 = client.get(f"/api/lacak/{slot.id}/telemetri", headers=headers)
    assert r1.status_code == 200, r1.text
    body1 = r1.json()
    assert len(body1["sampel"]) > 0
    assert body1["sampel"][0]["sumber"] == "SIMULASI"

    ringkasan = body1["ringkasan"]
    assert ringkasan is not None
    assert ringkasan["suhu_maks_c"] >= ringkasan["suhu_rata_c"]
    assert 0 <= ringkasan["sisa_umur_simpan_persen"] <= 100
    assert ringkasan["nama_komoditas"] == "Kubis"

    r2 = client.get(f"/api/lacak/{slot.id}/telemetri", headers=headers)
    assert r2.status_code == 200
    # Deterministik: dua panggilan menghasilkan data persis sama (baris tersimpan).
    assert r2.json()["sampel"] == body1["sampel"]


def test_telemetri_belum_ada_pengiriman_404(client, db, data_dasar, masuk):
    tk = data_dasar["titik_kumpul"]
    sekarang = datetime.now(timezone.utc)
    slot = Slot(
        kode="SM-TELEM-02",
        titik_kumpul_id=tk.id,
        # K13: petugas melihat muatan yang DITUGASKAN padanya.
        petugas_id=data_dasar["pengguna"]["titik_kumpul"].id,
        tanggal_kirim=sekarang.date(),
        cutoff_at=sekarang,
        status=StatusSlot.DIBUKA,
        jarak_km=Decimal("70.0"),
    )
    db.add(slot)
    db.commit()
    headers = masuk("081200000001")
    r = client.get(f"/api/lacak/{slot.id}/telemetri", headers=headers)
    assert r.status_code == 404
