"""Regresi K14 — mutu sebelum keputusan, tanpa potongan, TOLAK bersyarat.

Aturan produk yang dijaga di sini:

1. Penerima melihat **indeks mutu** sebelum memutuskan, bukan sesudah.
2. Tidak ada "terima dengan potongan" — API-nya pun tidak menerimanya lagi.
3. **TOLAK ditegakkan SERVER**, bukan sekadar tombolnya disembunyikan. Penerima
   yang memanggil API langsung tetap ditolak kalau penurunan mutu belum melewati
   ambang, karena kalau tidak, penerima bisa curang.
4. Perjalanan lengkap (timeline + telemetri) terbuka lewat resi — jalur lama
   berbasis `penerima_id` tidak lagi bisa dipakai sejak tujuan dibebaskan (K13).
"""

from datetime import date, datetime, timedelta, timezone

from app.models import Konfigurasi, Lot, Partisipasi, Pengiriman

BESOK = date.today() + timedelta(days=1)
CIBIRU = (-6.9269, 107.7189)
UJUNGBERUNG = (-6.9147, 107.7000)


def _muatan_jalan(client, data_dasar, masuk, kirim_panen) -> list[str]:
    """Satu muatan dua petani, diberangkatkan lewat tombol demo. -> daftar resi."""
    kubis = data_dasar["komoditas"]["kubis"]
    r1 = kirim_panen(masuk("081200000011"), kubis.id, 300, CIBIRU, BESOK)
    assert r1.status_code == 201, r1.text
    r2 = kirim_panen(masuk("081200000012"), kubis.id, 200, UJUNGBERUNG, BESOK)
    assert r2.status_code == 201, r2.text

    slot_id = r1.json()["slot_id"]
    header_petugas = masuk("081200000001")
    r = client.post(f"/api/demo/muatan/{slot_id}/berangkatkan", headers=header_petugas)
    assert r.status_code == 200, r.text
    pengiriman_id = r.json()["pengiriman_id"]
    for status in ("MUAT", "ANTAR", "BONGKAR_MUAT"):
        status_response = client.post(
            f"/api/pengiriman/{pengiriman_id}/status",
            headers=header_petugas,
            json={"status": status},
        )
        assert status_response.status_code == 200, status_response.text
    return r.json()["resi"]


def _lot_dari_resi(client, header, kode: str) -> dict:
    r = client.get(f"/api/lot/qr/{kode}", headers=header)
    assert r.status_code == 200, r.text
    return r.json()


def _perjalanan_sangat_terlambat(db, kode_resi: str) -> None:
    """Mundurkan waktu berangkat jauh ke belakang.

    Di dalam test seluruh perjalanan selesai dalam hitungan detik, jadi tidak
    ada penurunan mutu terukur dan cabang "boleh tolak" tidak pernah tersentuh.
    Memundurkan keberangkatan membuat waktu tempuh melewati ambang berkali-kali
    lipat — persis keadaan yang seharusnya membuka penolakan."""
    lot = db.query(Lot).filter_by(kode_qr=kode_resi).one()
    partisipasi = db.get(Partisipasi, lot.partisipasi_id)
    pengiriman = db.query(Pengiriman).filter_by(slot_id=partisipasi.slot_id).one()
    pengiriman.waktu_berangkat = datetime.now(timezone.utc) - timedelta(days=3)
    pengiriman.waktu_tiba = None
    db.commit()


def test_bukti_lot_membawa_indeks_mutu_sebelum_keputusan(client, data_dasar, masuk, kirim_panen):
    resi = _muatan_jalan(client, data_dasar, masuk, kirim_panen)
    bukti = _lot_dari_resi(client, masuk("081200000021"), resi[0])

    mutu = bukti["mutu"]
    assert bukti["serah_terima"] is None  # belum diputuskan
    assert 0 <= mutu["indeks_mutu"] <= 100
    assert mutu["penurunan_mutu_persen"] == 100 - mutu["indeks_mutu"]
    assert isinstance(mutu["boleh_tolak"], bool)
    assert len(mutu["alasan_boleh_tolak"]) > 20  # kalimat, bukan label


def test_tolak_ditolak_server_saat_mutu_masih_baik(client, data_dasar, masuk, kirim_panen):
    """Inti aturan: penerima TIDAK boleh menolak barang yang secara terukur
    masih baik, walau dia memanggil API langsung tanpa lewat tombol."""
    resi = _muatan_jalan(client, data_dasar, masuk, kirim_panen)
    header = masuk("081200000021")
    bukti = _lot_dari_resi(client, header, resi[0])
    assert bukti["mutu"]["boleh_tolak"] is False  # transit test = hitungan detik

    r = client.post(
        f"/api/lot/{bukti['lot']['id']}/serah-terima",
        headers=header,
        json={"keputusan": "TOLAK", "alasan": "Tidak suka.", "grade_tiba": 1},
    )
    assert r.status_code == 422, r.text
    assert "tidak boleh ditolak" in r.json()["detail"].lower()


def test_tolak_diterima_saat_ambang_dilewati(client, data_dasar, masuk, kirim_panen, db):
    """Kebalikannya harus juga benar — kalau tidak, gerbangnya cuma tembok mati."""
    resi = _muatan_jalan(client, data_dasar, masuk, kirim_panen)
    header = masuk("081200000021")
    _perjalanan_sangat_terlambat(db, resi[0])

    bukti = _lot_dari_resi(client, header, resi[0])
    assert bukti["mutu"]["boleh_tolak"] is True
    assert bukti["mutu"]["skor_transit"] == 0  # tiga hari untuk rute beberapa jam

    r = client.post(
        f"/api/lot/{bukti['lot']['id']}/serah-terima",
        headers=header,
        json={"keputusan": "TOLAK", "alasan": "Busuk saat tiba.", "grade_tiba": 1},
    )
    assert r.status_code == 201, r.text
    assert r.json()["keputusan"] == "TOLAK"


def test_potongan_tidak_lagi_diterima_api(client, data_dasar, masuk, kirim_panen):
    """K14: "terima dengan potongan" dicabut sampai ke kontrak."""
    resi = _muatan_jalan(client, data_dasar, masuk, kirim_panen)
    header = masuk("081200000021")
    bukti = _lot_dari_resi(client, header, resi[0])

    r = client.post(
        f"/api/lot/{bukti['lot']['id']}/serah-terima",
        headers=header,
        json={"keputusan": "POTONG", "persen_potongan": 20, "alasan": "Agak layu.", "grade_tiba": 3},
    )
    assert r.status_code == 422, r.text


def test_indeks_mutu_tercatat_di_serah_terima(client, data_dasar, masuk, kirim_panen):
    """Angka yang dilihat penerima harus tersimpan — supaya keputusannya bisa
    diaudit terhadap dasar yang sama, bukan dihitung ulang belakangan."""
    resi = _muatan_jalan(client, data_dasar, masuk, kirim_panen)
    header = masuk("081200000021")
    bukti = _lot_dari_resi(client, header, resi[0])
    indeks_terlihat = bukti["mutu"]["indeks_mutu"]

    r = client.post(
        f"/api/lot/{bukti['lot']['id']}/serah-terima",
        headers=header,
        json={"keputusan": "TERIMA", "grade_tiba": 4},
    )
    assert r.status_code == 201, r.text
    assert r.json()["indeks_mutu"] == indeks_terlihat


def test_perjalanan_terbuka_lewat_resi(client, data_dasar, masuk, kirim_panen):
    """Penerima berhak melihat SELURUH perjalanan sebelum memutuskan, termasuk
    untuk tujuan yang tidak tertaut ke akunnya."""
    resi = _muatan_jalan(client, data_dasar, masuk, kirim_panen)
    header = masuk("081200000021")

    for kode in resi:
        r = client.get(f"/api/lacak/resi/{kode}", headers=header)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["pengiriman"]["timeline"]["berangkat"] is not None
        assert body["titik_kumpul"]["lat"] != 0
        assert len(body["tujuan"]) >= 1
        assert "sampel" in body["telemetri"]

    assert client.get("/api/lacak/resi/LOT-TIDAK-ADA", headers=header).status_code == 404


def test_lot_ditolak_tidak_menutup_partisipasi_sebagai_selesai(
    client, data_dasar, masuk, kirim_panen, db
):
    """REGRESI: dulu lot yang DITOLAK tetap menandai partisipasi SELESAI dan
    muatan SELESAI — riwayat petani berbohong tentang apa yang terjadi."""
    resi = _muatan_jalan(client, data_dasar, masuk, kirim_panen)
    header = masuk("081200000021")
    _perjalanan_sangat_terlambat(db, resi[0])

    bukti = _lot_dari_resi(client, header, resi[0])
    assert bukti["mutu"]["boleh_tolak"] is True

    r = client.post(
        f"/api/lot/{bukti['lot']['id']}/serah-terima",
        headers=header,
        json={"keputusan": "TOLAK", "alasan": "Busuk saat tiba.", "grade_tiba": 1},
    )
    assert r.status_code == 201, r.text

    r_riwayat = client.get("/api/partisipasi/saya", headers=masuk("081200000011"))
    assert r_riwayat.status_code == 200, r_riwayat.text
    status_terkait = {
        p["status"] for p in r_riwayat.json() if p["id"] == bukti["lot"]["partisipasi_id"]
    }
    assert status_terkait == {"DITOLAK"}
