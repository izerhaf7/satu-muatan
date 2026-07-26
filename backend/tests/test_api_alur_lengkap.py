"""Test alur utuh: gabung -> tutup -> muat -> selesai-muat -> majukan -> serah terima.

Menguji bahwa penjelasan atribusi (§6) terisi kalimat, bukan cuma label, dan bahwa
Berita Acara + Dashboard Dampak ikut terisi setelah slot SELESAI.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models import Slot, SlotTujuan
from app.models.enums import StatusSlot


def _buat_slot_jarak_80(db, data_dasar, kode="SM-ALUR-01"):
    koperasi = data_dasar["koperasi"]
    cibiru = data_dasar["penerima"]["cibiru"]
    slot = Slot(
        kode=kode,
        koperasi_id=koperasi.id,
        tanggal_kirim=date.today() + timedelta(days=1),
        cutoff_at=datetime.now(timezone.utc) + timedelta(hours=6),
        status=StatusSlot.DIBUKA,
        jarak_km=Decimal("80.00"),
        volume_terkunci_kg=0,
        subsidi_koperasi=0,
    )
    db.add(slot)
    db.flush()
    db.add(SlotTujuan(slot_id=slot.id, penerima_id=cibiru.id, urutan=1, jarak_segmen_km=Decimal("80.00")))
    db.commit()
    db.refresh(slot)
    return slot


def test_alur_penuh_gabung_sampai_serah_terima(client, data_dasar, masuk, db):
    slot = _buat_slot_jarak_80(db, data_dasar)
    kubis_id = str(data_dasar["komoditas"]["kubis"].id)

    header_koperasi = masuk("081200000001")
    header_asep = masuk("081200000011")
    header_penerima = masuk("081200000021")

    # 1) Asep gabung 800 kg kubis (VAN penuh persis -> biaya habis dibagi rata,
    # subsidi_koperasi = 0 bersih; volume yang tidak habis dibagi wajar punya sisa
    # pembulatan kecil dari ceil() dan diuji terpisah, bukan di sini).
    r = client.post(
        f"/api/slot/{slot.id}/gabung", headers=header_asep, json={"komoditas_id": kubis_id, "volume_kg": 800}
    )
    assert r.status_code == 201, r.text
    atap = r.json()["harga_atap_per_kg"]
    assert atap == 415  # K1 T4: 800 kg -> VAN 332.000 -> ceil(332000/800)=415

    # 2) Koperasi tutup slot -> harga final, lot, pengiriman.
    r = client.post(f"/api/slot/{slot.id}/tutup", headers=header_koperasi)
    assert r.status_code == 200, r.text
    tutup = r.json()
    assert tutup["status"] == "TERKUNCI"
    assert tutup["harga_final_per_kg"] == atap  # satu peserta -> H_kasar == atap, tidak ada subsidi
    assert tutup["subsidi_koperasi"] == 0
    assert tutup["partisipasi"][0]["kembalian_rp"] == 0

    r = client.get(f"/api/slot/{slot.id}/lot", headers=header_koperasi)
    lots = r.json()
    assert len(lots) == 1
    lot_id = lots[0]["id"]
    kode_qr = lots[0]["kode_qr"]
    assert kode_qr == f"LOT-{slot.kode}-01"
    assert lots[0]["penerima_id"] is not None

    # 3) Muat: timbang + foto, tanpa cacat.
    r = client.patch(
        f"/api/lot/{lot_id}/muat",
        headers=header_koperasi,
        json={"berat_aktual_kg": 795, "foto_muat_base64": "ZmFrZS1mb3RvLW11YXQ=", "cacat_terlihat": False, "catatan_muat": "kondisi baik"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["berat_aktual_kg"] == 795
    assert r.json()["waktu_muat"]

    r = client.get(f"/api/slot/{slot.id}", headers=header_koperasi)
    assert r.json()["status"] == "DIMUAT"

    # 4) Selesai muat -> slot JALAN, pengiriman berangkat.
    r = client.post(f"/api/slot/{slot.id}/selesai-muat", headers=header_koperasi)
    assert r.status_code == 200, r.text
    assert r.json()[0]["waktu_muat"]

    r = client.get(f"/api/slot/{slot.id}", headers=header_koperasi)
    assert r.json()["status"] == "JALAN"

    r = client.get(f"/api/slot/{slot.id}/pengiriman", headers=header_koperasi)
    assert r.status_code == 200, r.text
    pengiriman = r.json()
    assert pengiriman["status_vendor"] == "JALAN"
    assert pengiriman["timeline"]["berangkat"]
    assert pengiriman["estimasi_tiba"]
    assert pengiriman["ambang_transit_menit"] > 0
    pengiriman_id = pengiriman["id"]

    # 5) Majukan -> TIBA (sim K5), jejak posisi tercatat.
    r = client.post(f"/api/pengiriman/{pengiriman_id}/majukan", headers=header_koperasi)
    assert r.status_code == 200, r.text
    maju = r.json()
    assert maju["status_vendor"] == "TIBA"
    assert maju["timeline"]["tiba"]
    assert len(maju["jejak"]) >= 1
    assert maju["jejak"][-1]["sumber"] == "SIMULASI"

    # Memanggil lagi setelah TIBA harus idempoten (tidak error).
    r = client.post(f"/api/pengiriman/{pengiriman_id}/majukan", headers=header_koperasi)
    assert r.status_code == 200
    assert r.json()["status_vendor"] == "TIBA"

    # 6) Penerima: lihat lot masuk, ambil bukti dari QR.
    r = client.get("/api/lot/masuk", headers=header_penerima)
    assert r.status_code == 200
    assert any(b["lot"]["id"] == lot_id for b in r.json())

    r = client.get(f"/api/lot/qr/{kode_qr}", headers=header_penerima)
    assert r.status_code == 200, r.text
    bukti = r.json()
    assert bukti["serah_terima"] is None
    assert bukti["durasi_transit_berjalan_menit"] is not None
    assert bukti["ambang_transit_menit"] > 0

    # 7) Serah terima -> atribusi + PENJELASAN kalimat, bukan label doang (§6).
    r = client.post(
        f"/api/lot/{lot_id}/serah-terima",
        headers=header_penerima,
        json={"keputusan": "TERIMA", "persen_potongan": 0, "alasan": None, "foto_bongkar_base64": "ZmFrZS1mb3RvLWJvbmdrYXI="},
    )
    assert r.status_code == 201, r.text
    st = r.json()
    assert st["atribusi"] in ("TIDAK_TERBUKTI", "LOGISTIK")  # tidak ada cacat terlihat -> bukan PETANI
    assert isinstance(st["penjelasan"], str) and len(st["penjelasan"]) > 20
    assert str(st["durasi_transit_menit"]) in st["penjelasan"]
    assert str(st["ambang_transit_menit"]) in st["penjelasan"]

    # Tidak boleh diserahterimakan dua kali.
    r_dobel = client.post(
        f"/api/lot/{lot_id}/serah-terima",
        headers=header_penerima,
        json={"keputusan": "TERIMA", "persen_potongan": 0, "foto_bongkar_base64": None},
    )
    assert r_dobel.status_code == 409

    # 8) Slot & partisipasi selesai (semua lot sudah diserahterimakan).
    r = client.get(f"/api/slot/{slot.id}", headers=header_koperasi)
    detail = r.json()
    assert detail["status"] == "SELESAI"
    assert detail["partisipasi"][0]["status"] == "SELESAI"

    # 9) Riwayat partisipasi Asep.
    r = client.get("/api/partisipasi/saya", headers=header_asep)
    assert r.status_code == 200
    riwayat = r.json()
    assert len(riwayat) == 1
    assert riwayat[0]["status"] == "SELESAI"
    assert riwayat[0]["slot_kode"] == slot.kode

    # 10) Berita Acara.
    r = client.get(f"/api/slot/{slot.id}/berita-acara", headers=header_koperasi)
    assert r.status_code == 200, r.text
    ba = r.json()
    assert ba["kode_slot"] == slot.kode
    assert len(ba["lot"]) == 1
    assert ba["lot"][0]["serah_terima"] is not None
    assert len(ba["rincian_ongkos"]) == 1
    assert ba["rincian_ongkos"][0]["nama_petani"] == "Asep"

    # 11) Dashboard Dampak — satu peserta -> truk_km & penghematan = 0 (bukan null,
    # karena ADA data), susut terisi dari jam_dihemat_per_kirim (K6).
    r = client.get("/api/dampak/ringkasan", headers=header_koperasi)
    assert r.status_code == 200, r.text
    ringkasan = r.json()
    assert ringkasan["truk_km_dihemat"]["nilai"] == 0
    assert ringkasan["penghematan_ongkos_rp"]["nilai"] == 0
    assert ringkasan["susut_dicegah_kg"]["nilai"] is not None
    assert ringkasan["susut_dicegah_kg"]["nilai"] == pytest.approx(800 * 0.00250 * 4.0)

    r = client.get("/api/dampak/bulanan", headers=header_koperasi)
    assert r.status_code == 200
    bulanan = r.json()
    assert len(bulanan) == 1
    assert bulanan[0]["jumlah_kiriman"] == 1
    assert bulanan[0]["susut_kg"] is not None
