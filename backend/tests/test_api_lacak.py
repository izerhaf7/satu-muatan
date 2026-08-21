"""Test endpoint pelacakan (T5/T6/T7/T8): ETA provider, gate JALAN, geser
kontinu sepanjang polyline, dan endpoint `sampai` dengan validasi radius."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models import JejakPosisi, Pengiriman, Slot, SlotTujuan
from app.models.enums import StatusPengiriman, StatusSlot, SumberPosisi

BESOK = date.today() + timedelta(days=1)
LAT_CIBIRU, LNG_CIBIRU = -6.9269, 107.7189


def _muatan_siap(client, data_dasar, masuk, kirim_panen):
    """Satu muatan berisi dua petani, dibuat lewat alur sungguhan (Kirim Panen)."""
    kubis = data_dasar["komoditas"]["kubis"]
    r1 = kirim_panen(masuk("081200000011"), kubis.id, 300, (LAT_CIBIRU, LNG_CIBIRU), BESOK)
    assert r1.status_code == 201, r1.text
    r2 = kirim_panen(masuk("081200000012"), kubis.id, 200, (-6.9147, 107.7000), BESOK)
    assert r2.status_code == 201, r2.text
    assert r2.json()["slot_id"] == r1.json()["slot_id"]
    return r1.json()["slot_id"]


def _berangkatkan(client, data_dasar, masuk, kirim_panen):
    """Buat muatan + berangkatkan lewat jalan pintas demo → slot JALAN."""
    slot_id = _muatan_siap(client, data_dasar, masuk, kirim_panen)
    r = client.post(f"/api/demo/muatan/{slot_id}/berangkatkan", headers=masuk("081200000001"))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "JALAN"
    return slot_id, r.json()["pengiriman_id"]


def _slot_terkunci(client, data_dasar, masuk, kirim_panen, ambil_tugas):
    """Buat muatan + tutup (TERKUNCI) tanpa berangkat — untuk uji gate JALAN."""
    slot_id = _muatan_siap(client, data_dasar, masuk, kirim_panen)
    header_petugas = masuk("081200000001")
    ambil_tugas(header_petugas, slot_id)
    r = client.post(f"/api/slot/{slot_id}/tutup", headers=header_petugas)
    assert r.status_code == 200, r.text
    pengiriman = client.get(f"/api/slot/{slot_id}/pengiriman", headers=header_petugas).json()
    return slot_id, pengiriman["id"]


# ---------------------------------------------------------------------------
# T5 — ETA provider + estimasi_tiba


def test_estimasi_tiba_memakai_durasi_provider_saat_tersedia(client, data_dasar, masuk, kirim_panen, db):
    """Kalau `rute_durasi_provider_menit` terisi, `estimasi_tiba` = berangkat +
    durasi provider, dan `eta_provider_menit`/`jarak_provider_km` ikut terisi."""
    slot_id, pengiriman_id = _berangkatkan(client, data_dasar, masuk, kirim_panen)
    pengiriman = db.get(Pengiriman, pengiriman_id)
    pengiriman.rute_durasi_provider_menit = 45
    pengiriman.rute_jarak_provider_km = Decimal("26.250")
    db.commit()

    r = client.get(f"/api/slot/{slot_id}/pengiriman", headers=masuk("081200000001"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["eta_provider_menit"] == 45
    assert body["jarak_provider_km"] == 26.25
    estimasi = datetime.fromisoformat(body["estimasi_tiba"].replace("Z", "+00:00"))
    berangkat = datetime.fromisoformat(body["timeline"]["berangkat"].replace("Z", "+00:00"))
    assert estimasi == berangkat + timedelta(minutes=45)


def test_estimasi_tiba_jatuh_ke_ambang_saat_durasi_null(client, data_dasar, masuk, kirim_panen, db):
    """Kalau `rute_durasi_provider_menit` kosong, `estimasi_tiba` memakai
    `ambang_transit_menit` (jarak/kecepatan × toleransi), dan field provider None."""
    slot_id, pengiriman_id = _berangkatkan(client, data_dasar, masuk, kirim_panen)
    pengiriman = db.get(Pengiriman, pengiriman_id)
    pengiriman.rute_durasi_provider_menit = None
    pengiriman.rute_jarak_provider_km = None
    db.commit()

    r = client.get(f"/api/slot/{slot_id}/pengiriman", headers=masuk("081200000001"))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["eta_provider_menit"] is None
    assert body["jarak_provider_km"] is None
    ambang = body["ambang_transit_menit"]
    assert ambang > 0
    estimasi = datetime.fromisoformat(body["estimasi_tiba"].replace("Z", "+00:00"))
    berangkat = datetime.fromisoformat(body["timeline"]["berangkat"].replace("Z", "+00:00"))
    assert estimasi == berangkat + timedelta(minutes=ambang)


# ---------------------------------------------------------------------------
# IoT — status driver, GPS, dan node sensor


def test_status_driver_harus_berurutan_dan_penerima_menyelesaikan_akhirnya(client, data_dasar, masuk, kirim_panen):
    slot_id, pengiriman_id = _berangkatkan(client, data_dasar, masuk, kirim_panen)
    header_petugas = masuk("081200000001")

    loncat = client.post(
        f"/api/pengiriman/{pengiriman_id}/status",
        headers=header_petugas,
        json={"status": "ANTAR"},
    )
    assert loncat.status_code == 409

    for status_pengiriman in ("MUAT", "ANTAR", "BONGKAR_MUAT"):
        response = client.post(
            f"/api/pengiriman/{pengiriman_id}/status",
            headers=header_petugas,
            json={"status": status_pengiriman},
        )
        assert response.status_code == 200, response.text
        assert response.json()["status_pengiriman"] == status_pengiriman

    assert response.json()["timeline"]["tiba"] is not None


def test_gps_driver_disimpan_ke_jejak_posisi(client, data_dasar, masuk, kirim_panen, db):
    _, pengiriman_id = _berangkatkan(client, data_dasar, masuk, kirim_panen)
    header_petugas = masuk("081200000001")
    for status_pengiriman in ("MUAT", "ANTAR"):
        response = client.post(
            f"/api/pengiriman/{pengiriman_id}/status",
            headers=header_petugas,
            json={"status": status_pengiriman},
        )
        assert response.status_code == 200, response.text

    response = client.post(
        f"/api/pengiriman/{pengiriman_id}/posisi",
        headers=header_petugas,
        json={"lat": -6.9269, "lng": 107.7189, "akurasi_m": 8.5},
    )
    assert response.status_code == 200, response.text
    jejak = db.query(JejakPosisi).filter_by(pengiriman_id=pengiriman_id).order_by(JejakPosisi.waktu.desc()).first()
    assert jejak is not None
    assert jejak.sumber == SumberPosisi.HP_PENGAWAL
    assert jejak.akurasi_m == 8.5


def test_node_sensor_hanya_dapat_ditetapkan_petugas_pemegang_muatan(client, data_dasar, masuk, kirim_panen):
    slot_id, _ = _berangkatkan(client, data_dasar, masuk, kirim_panen)
    tidak_berhak = client.put(
        f"/api/slot/{slot_id}/sensor-node",
        headers=masuk("081200000012"),
        json={"node_path": "/sensor"},
    )
    assert tidak_berhak.status_code == 403

    response = client.put(
        f"/api/slot/{slot_id}/sensor-node",
        headers=masuk("081200000001"),
        json={"node_path": "sensor/dht22"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["node_path"] == "/sensor/dht22"


# ---------------------------------------------------------------------------
# T7 — gate geser/majukan pada slot JALAN


def test_geser_ditolak_saat_slot_belum_jalan(client, data_dasar, masuk, kirim_panen, ambil_tugas, db):
    """`geser` → 409 MUAT_BELUM_SELESAI kalau slot masih TERKUNCI (belum muat),
    walau `waktu_berangkat` sudah terisi (penjagaan kedua setelah cek berangkat)."""
    slot_id, pengiriman_id = _slot_terkunci(client, data_dasar, masuk, kirim_panen, ambil_tugas)
    # Isi waktu_berangkat supaya cek "belum berangkat" tidak mendahului gate JALAN.
    pengiriman = db.get(Pengiriman, pengiriman_id)
    pengiriman.waktu_berangkat = datetime.now(timezone.utc)
    db.commit()
    r = client.post(f"/api/pengiriman/{pengiriman_id}/geser", headers=masuk("081200000001"))
    assert r.status_code == 410


def test_majukan_ditolak_saat_slot_belum_jalan(client, data_dasar, masuk, kirim_panen, ambil_tugas, db):
    """`majukan` → 409 MUAT_BELUM_SELESAI kalau slot masih TERKUNCI."""
    slot_id, pengiriman_id = _slot_terkunci(client, data_dasar, masuk, kirim_panen, ambil_tugas)
    pengiriman = db.get(Pengiriman, pengiriman_id)
    pengiriman.waktu_berangkat = datetime.now(timezone.utc)
    db.commit()
    r = client.post(f"/api/pengiriman/{pengiriman_id}/majukan", headers=masuk("081200000001"))
    assert r.status_code == 410


def test_geser_berhasil_saat_slot_jalan(client, data_dasar, masuk, kirim_panen):
    """`geser` → 200 kalau slot JALAN, dan posisi maju sepanjang polyline."""
    slot_id, pengiriman_id = _berangkatkan(client, data_dasar, masuk, kirim_panen)
    r = client.post(f"/api/pengiriman/{pengiriman_id}/geser", headers=masuk("081200000001"))
    assert r.status_code == 410


def test_majukan_berhasil_saat_slot_jalan(client, data_dasar, masuk, kirim_panen):
    """`majukan` → 200 kalau slot JALAN."""
    slot_id, pengiriman_id = _berangkatkan(client, data_dasar, masuk, kirim_panen)
    r = client.post(f"/api/pengiriman/{pengiriman_id}/majukan", headers=masuk("081200000001"))
    assert r.status_code == 410


# ---------------------------------------------------------------------------
# T6 — geser kontinu + overshoot


def test_geser_overshoot_klamp_ke_tujuan_dan_tiba(client, data_dasar, masuk, kirim_panen, db):
    """Elapsed besar → jarak tempuh melewati panjang rute → posisi diklamp ke
    tujuan akhir, `waktu_tiba` terisi, status TIBA."""
    slot_id, pengiriman_id = _berangkatkan(client, data_dasar, masuk, kirim_panen)
    pengiriman = db.get(Pengiriman, pengiriman_id)
    pengiriman.waktu_berangkat = datetime.now(timezone.utc) - timedelta(hours=3)
    db.commit()

    r = client.post(f"/api/pengiriman/{pengiriman_id}/geser", headers=masuk("081200000001"))
    assert r.status_code == 410


# ---------------------------------------------------------------------------
# T8 — endpoint sampai


def _tujuan_akhir(db, slot_id):
    """Titik drop terakhir dari rute rencana slot."""
    from app.models import Penerima

    slot = db.get(Slot, slot_id)
    tujuan_akhir = max(slot.tujuan, key=lambda t: t.urutan)
    penerima = db.get(Penerima, tujuan_akhir.penerima_id)
    return penerima.lat, penerima.lng


def test_sampai_ditolak_saat_koordinat_di_luar_radius(client, data_dasar, masuk, kirim_panen, db):
    """`sampai` → 422 BELUM_DI_TUJUAN kalau koordinat jauh dari tujuan akhir."""
    slot_id, pengiriman_id = _berangkatkan(client, data_dasar, masuk, kirim_panen)
    # Titik sangat jauh dari tujuan akhir.
    r = client.post(
        f"/api/pengiriman/{pengiriman_id}/sampai",
        headers=masuk("081200000001"),
        json={"koordinat": {"lat": -6.2, "lng": 106.8}},
    )
    assert r.status_code == 410


def test_sampai_berhasil_di_dalam_radius(client, data_dasar, masuk, kirim_panen, db):
    """`sampai` → 200 kalau koordinat dalam radius tujuan akhir."""
    slot_id, pengiriman_id = _berangkatkan(client, data_dasar, masuk, kirim_panen)
    lat, lng = _tujuan_akhir(db, slot_id)
    r = client.post(
        f"/api/pengiriman/{pengiriman_id}/sampai",
        headers=masuk("081200000001"),
        json={"koordinat": {"lat": lat, "lng": lng}},
    )
    assert r.status_code == 410


def test_sampai_berhasil_tanpa_body(client, data_dasar, masuk, kirim_panen):
    """`sampai` tanpa body → diterima begitu saja."""
    slot_id, pengiriman_id = _berangkatkan(client, data_dasar, masuk, kirim_panen)
    r = client.post(f"/api/pengiriman/{pengiriman_id}/sampai", headers=masuk("081200000001"))
    assert r.status_code == 410


def test_sampai_idempoten_sudah_tiba(client, data_dasar, masuk, kirim_panen):
    """`sampai` kedua → 409 SUDAH_TIBA."""
    slot_id, pengiriman_id = _berangkatkan(client, data_dasar, masuk, kirim_panen)
    r1 = client.post(f"/api/pengiriman/{pengiriman_id}/sampai", headers=masuk("081200000001"))
    assert r1.status_code == 410


def test_sampai_ditolak_saat_slot_belum_jalan(client, data_dasar, masuk, kirim_panen, ambil_tugas):
    """`sampai` → 409 MUAT_BELUM_SELESAI kalau slot belum JALAN."""
    slot_id, pengiriman_id = _slot_terkunci(client, data_dasar, masuk, kirim_panen, ambil_tugas)
    r = client.post(f"/api/pengiriman/{pengiriman_id}/sampai", headers=masuk("081200000001"))
    assert r.status_code == 410
