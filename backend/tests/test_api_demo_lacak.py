"""Test alur demo pelacakan (K13, tambahan demo):
tombol berangkatkan → resi terbit → posisi digeser → peta bergerak → tiba.

Ini menutup temuan bahwa `jejak` selalu kosong: dulu titik posisi hanya ditulis
SATU KALI saat TIBA, dan keberangkatan melompati state machine sama sekali.
"""

from datetime import date, timedelta

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


def test_berangkatkan_demo_menerbitkan_resi(client, data_dasar, masuk, kirim_panen):
    slot_id = _muatan_siap(client, data_dasar, masuk, kirim_panen)
    header_petugas = masuk("081200000001")

    r = client.post(f"/api/demo/muatan/{slot_id}/berangkatkan", headers=header_petugas)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "JALAN"
    assert body["pengiriman_id"] is not None
    assert len(body["resi"]) == 2
    assert all(kode.startswith("LOT-SM-") for kode in body["resi"])


def test_penerima_melacak_lewat_resi_tanpa_ikatan_alamat(client, data_dasar, masuk, kirim_panen):
    """K13: memegang resi = berhak melihat. Tujuan Wati (Ujungberung) BUKAN
    alamat yang tertaut ke akun Bu Rina, tapi resinya tetap bisa dilacak."""
    slot_id = _muatan_siap(client, data_dasar, masuk, kirim_panen)
    r = client.post(f"/api/demo/muatan/{slot_id}/berangkatkan", headers=masuk("081200000001"))
    assert r.status_code == 200, r.text

    header_rina = masuk("081200000021")
    for kode in r.json()["resi"]:
        rr = client.get(f"/api/lot/qr/{kode}", headers=header_rina)
        assert rr.status_code == 200, rr.text
        assert rr.json()["lot"]["kode_qr"] == kode

    rr = client.get("/api/lot/qr/LOT-TIDAK-ADA-01", headers=header_rina)
    assert rr.status_code == 404


def test_geser_posisi_menggerakkan_peta_sampai_tiba(client, data_dasar, masuk, kirim_panen, db):
    """REGRESI: dulu `jejak` selalu [] sampai TIBA sehingga peta tidak pernah
    bergerak. Sekarang tiap geser menambah titik jejak, dan begitu jarak tempuh
    melewati panjang rute, muatan ditandai TIBA."""
    from datetime import datetime, timedelta, timezone

    from app.models import Pengiriman

    slot_id = _muatan_siap(client, data_dasar, masuk, kirim_panen)
    header_petugas = masuk("081200000001")
    r = client.post(f"/api/demo/muatan/{slot_id}/berangkatkan", headers=header_petugas)
    pengiriman_id = r.json()["pengiriman_id"]

    # Titik jejak pertama sudah tercatat saat berangkat (dari titik kumpul).
    jejak_awal = client.get(f"/api/slot/{slot_id}/pengiriman", headers=header_petugas).json()["jejak"]
    assert len(jejak_awal) == 1, "keberangkatan wajib mencatat titik awal"

    # Fitur gerak simulasi dinonaktifkan; lokasi kini berasal dari GPS driver.
    pengiriman = db.get(Pengiriman, pengiriman_id)
    pengiriman.waktu_berangkat = datetime.now(timezone.utc) - timedelta(hours=2)
    db.commit()

    rg = client.post(f"/api/pengiriman/{pengiriman_id}/geser", headers=header_petugas)
    assert rg.status_code == 410

    # Endpoint lama tetap disabled.
    rg2 = client.post(f"/api/pengiriman/{pengiriman_id}/geser", headers=header_petugas)
    assert rg2.status_code == 410


def test_geser_ditolak_sebelum_berangkat(client, data_dasar, masuk, kirim_panen, ambil_tugas):
    slot_id = _muatan_siap(client, data_dasar, masuk, kirim_panen)
    header_petugas = masuk("081200000001")
    # K14: muatan lahir tanpa driver — ambil tugasnya dulu.
    ambil_tugas(header_petugas, slot_id)
    r_tutup = client.post(f"/api/slot/{slot_id}/tutup", headers=header_petugas)
    assert r_tutup.status_code == 200, r_tutup.text
    pengiriman = client.get(f"/api/slot/{slot_id}/pengiriman", headers=header_petugas).json()

    r = client.post(f"/api/pengiriman/{pengiriman['id']}/geser", headers=header_petugas)
    assert r.status_code == 410
