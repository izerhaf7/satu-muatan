"""Test integrasi skenario demo §11.2 (13 langkah) + butir Definition of Done §14
yang bisa diverifikasi lewat API murni (jaminan atap, dialog LUAPAN_KAPASITAS).

Angka acuan dihitung ULANG dari mesin harga sebenarnya (bukan disalin dari spec —
spec §11.2 eksplisit menandai angka langkah 4-6 sebagai ilustrasi lama, dan
KEPUTUSAN.md K2 sudah mengoreksinya):

  Rute nearest-neighbor gudang -> {Cibiru 3, Ujungberung 1, Panyileukan 2}
  (koordinat seed §11.1, faktor_jalan 1,30) = 70,03 km (K2).

  Deret gabung pada 70,03 km:
    Asep gabung 300 kg (total 300)  -> atap terkunci   Rp1.007/kg
    Wati gabung 200 kg (total 500)  -> harga berjalan  Rp605/kg
    Dedi gabung 180 kg (total 680)  -> harga berjalan  Rp445/kg
    Ijah gabung 100 kg (total 780)  -> harga berjalan  Rp388/kg
    Asep hemat = 1.007 - 388 = Rp619/kg -> 300 x 619 = Rp185.700 kembalian

  Tutup slot @780 kg -> VAN (kapasitas 800), biaya_total 302.090, H_kasar 388.
  Atap individu semua peserta (1.007 / 1.511 / 1.679 / 2.421) > 388, jadi jaminan
  atap TIDAK aktif untuk siapa pun -> H_i = 388 untuk semua. selisih_jaminan_atap
  dari mesin adalah biaya_total - Σ(volume_i x 388) = 302.090 - 302.640 = -550
  (bukan 0!) -- konsekuensi pembulatan ceil() pada H_kasar, diverifikasi lewat
  perhitungan exhaustive terhadap app.domain.harga sebelum ditulis di sini
  (lihat catatan temuan penguji: selisih_jaminan_atap negatif tidak pernah
  diantisipasi narasi "selisih ditanggung titik_kumpul" di §5.5/§9.8).

Dampak (4 peserta, 1 slot SELESAI):
  truk_km_dihemat      = (4-1) x 70,03           = 210,09
  emisi_dihemat_kg_co2 = 210,09 x 0,25            = 52,5225
  penghematan_ongkos_rp = Σ kembalian             = 845.980
  susut_dicegah_kg     = 780 x 0,00250 x 4,0      = 7,8
"""

from datetime import date, datetime, timedelta, timezone

import pytest

PIN = "123456"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _besok() -> date:
    return date.today() + timedelta(days=1)


def _cutoff() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=6)).isoformat()


def _tujuan_3_sppg(data_dasar) -> list[str]:
    penerima = data_dasar["penerima"]
    return [str(penerima["cibiru"].id), str(penerima["ujungberung"].id), str(penerima["panyileukan"].id)]


def _buat_muatan_3_tujuan(db, data_dasar, kode="SM-DEMO-01"):
    """Muatan 3 tujuan dengan rute nearest-neighbor SUNGGUHAN (= 70,03 km, K2).

    K13 menghapus `POST /api/slot`: muatan lahir dari kiriman petani dan selalu
    mulai dari satu tujuan. Untuk test angka acuan K1/K2 kita tetap butuh rute
    3-tujuan yang persis sama, jadi muatannya dirakit langsung lewat ORM memakai
    fungsi rute yang sama dengan yang dipakai produksi — bukan angka yang diketik
    ulang di sini (CLAUDE.md aturan #1).
    """
    from decimal import Decimal

    from app.domain.armada import TujuanInput, urutkan_tujuan_nearest_neighbor
    from app.models import Slot, SlotTujuan
    from app.models.enums import StatusSlot
    from app.services.konfigurasi import baca_konfigurasi

    tk = data_dasar["titik_kumpul"]
    penerima = data_dasar["penerima"]
    faktor_jalan = baca_konfigurasi(db, "faktor_jalan")
    urutan = urutkan_tujuan_nearest_neighbor(
        (tk.lat, tk.lng),
        [
            TujuanInput(penerima_id=p.id, lat=p.lat, lng=p.lng)
            for p in (penerima["cibiru"], penerima["ujungberung"], penerima["panyileukan"])
        ],
        faktor_jalan,
    )
    jarak_total = sum(t.jarak_segmen_km for t in urutan)

    slot = Slot(
        kode=kode,
        titik_kumpul_id=tk.id,
        petugas_id=data_dasar["pengguna"]["titik_kumpul"].id,
        tanggal_kirim=_besok(),
        cutoff_at=datetime.now(timezone.utc) + timedelta(hours=6),
        status=StatusSlot.DIBUKA,
        jarak_km=Decimal(str(round(jarak_total, 2))),
        volume_terkunci_kg=0,
        selisih_jaminan_atap=0,
    )
    db.add(slot)
    db.flush()
    for t in urutan:
        db.add(
            SlotTujuan(
                slot_id=slot.id,
                penerima_id=t.penerima_id,
                urutan=t.urutan,
                jarak_segmen_km=Decimal(str(round(t.jarak_segmen_km, 2))),
            )
        )
    db.commit()
    db.refresh(slot)
    return slot


# ---------------------------------------------------------------------------
# Skenario demo §11.2 penuh, 13 langkah, via TestClient murni (tanpa sentuh DB
# manual selain fixture data induk) -- DoD butir "Skenario demo §11.2 bisa
# dijalankan penuh tanpa menyentuh database manual".
# ---------------------------------------------------------------------------


def test_skenario_demo_11_2_end_to_end(client, data_dasar, masuk, db):
    kubis_id = str(data_dasar["komoditas"]["kubis"].id)

    header_rina = masuk("081200000021")  # PENERIMA (Kepala Dapur)
    header_titik_kumpul = masuk("081200000001")  # Bu Nia — petugas/driver
    header_asep = masuk("081200000011")
    header_wati = masuk("081200000012")
    header_dedi = masuk("081200000013")
    header_ijah = masuk("081200000014")

    # -----------------------------------------------------------------
    # Langkah 1-2 (K13): tidak ada lagi "penerima memesan" maupun "petugas
    # membuka slot". Muatan adalah lapisan abstraksi — di sini dirakit langsung
    # dengan rute 3 tujuan supaya angka acuan K1/K2 (70,03 km) tetap teruji.
    # -----------------------------------------------------------------
    slot_row = _buat_muatan_3_tujuan(db, data_dasar)
    slot_id = str(slot_row.id)

    r = client.get(f"/api/slot/{slot_id}", headers=header_titik_kumpul)
    assert r.status_code == 200, r.text
    slot = r.json()
    assert slot["status"] == "DIBUKA"
    assert slot["jarak_km"] == pytest.approx(70.03, abs=0.1)  # K2: rute nearest-neighbor seed §11.1

    # -----------------------------------------------------------------
    # Langkah 3: Asep ikut kirim 300 kg -> HARGA ATAP TERKUNCI Rp1.007/kg.
    # -----------------------------------------------------------------
    r = client.post(
        f"/api/slot/{slot_id}/gabung", headers=header_asep, json={"komoditas_id": kubis_id, "volume_kg": 300}
    )
    assert r.status_code == 201, r.text
    assert r.json()["harga_atap_per_kg"] == 1007

    r = client.get(f"/api/slot/{slot_id}", headers=header_asep)
    assert r.json()["atap_saya_per_kg"] == 1007

    # -----------------------------------------------------------------
    # Langkah 4: Wati ikut 200 kg (total 500) -> harga berjalan turun ke
    # Rp605/kg. Atap Asep TIDAK berubah (DoD: "harga atap tidak pernah
    # berubah setelah petani bergabung — diuji, bukan diasumsikan").
    # -----------------------------------------------------------------
    r = client.post(
        f"/api/slot/{slot_id}/gabung", headers=header_wati, json={"komoditas_id": kubis_id, "volume_kg": 200}
    )
    assert r.status_code == 201, r.text

    r = client.get(f"/api/slot/{slot_id}", headers=header_titik_kumpul)
    assert r.json()["harga_berjalan_per_kg"] == 605

    r = client.get(f"/api/slot/{slot_id}", headers=header_asep)
    assert r.json()["atap_saya_per_kg"] == 1007  # tidak berubah

    # -----------------------------------------------------------------
    # Langkah 5: Dedi ikut 180 kg (total 680) -> harga berjalan turun ke
    # Rp445/kg. Atap Asep masih tidak berubah.
    # -----------------------------------------------------------------
    r = client.post(
        f"/api/slot/{slot_id}/gabung", headers=header_dedi, json={"komoditas_id": kubis_id, "volume_kg": 180}
    )
    assert r.status_code == 201, r.text

    r = client.get(f"/api/slot/{slot_id}", headers=header_titik_kumpul)
    assert r.json()["harga_berjalan_per_kg"] == 445

    r = client.get(f"/api/slot/{slot_id}", headers=header_asep)
    assert r.json()["atap_saya_per_kg"] == 1007  # tidak berubah

    # -----------------------------------------------------------------
    # Langkah 6: Ijah ikut 100 kg (total 780) -> harga berjalan turun ke
    # Rp388/kg. Layar Asep: "Kamu hemat Rp619/kg".
    # -----------------------------------------------------------------
    r = client.post(
        f"/api/slot/{slot_id}/gabung", headers=header_ijah, json={"komoditas_id": kubis_id, "volume_kg": 100}
    )
    assert r.status_code == 201, r.text

    r = client.get(f"/api/slot/{slot_id}", headers=header_titik_kumpul)
    assert r.json()["volume_total_kg"] == 780
    assert r.json()["harga_berjalan_per_kg"] == 388

    r = client.get(f"/api/slot/{slot_id}", headers=header_asep)
    detail_asep = r.json()
    assert detail_asep["atap_saya_per_kg"] == 1007  # tidak pernah berubah, sampai akhir
    assert detail_asep["hemat_saya_per_kg"] == 619

    # -----------------------------------------------------------------
    # Langkah 7: Bu Nia tutup slot -> sistem memilih VAN, harga final
    # Rp388/kg, kembalian Asep = 300 x 619 = Rp185.700.
    # -----------------------------------------------------------------
    r = client.post(f"/api/slot/{slot_id}/tutup", headers=header_titik_kumpul)
    assert r.status_code == 200, r.text
    tutup = r.json()
    assert tutup["status"] == "TERKUNCI"
    assert tutup["harga_final_per_kg"] == 388
    assert tutup["biaya_total"] == 302_090
    assert [t["kode"] for t in tutup["rencana_saat_ini"]["tier"]] == ["VAN"]
    # selisih_jaminan_atap TERUKUR -550 (bukan 0/positif) -- lihat catatan modul
    # di atas: konsekuensi pembulatan ceil() saat H_kasar dikali volume genap.
    assert tutup["selisih_jaminan_atap"] == -550

    by_petani = {p["nama_petani"]: p for p in tutup["partisipasi"]}
    assert by_petani["Asep"]["kembalian_rp"] == 185_700
    assert by_petani["Asep"]["harga_final_per_kg"] == 388
    assert by_petani["Wati"]["kembalian_rp"] == 224_600
    assert by_petani["Dedi"]["kembalian_rp"] == 232_380
    assert by_petani["Ijah"]["kembalian_rp"] == 203_300

    r = client.get(f"/api/slot/{slot_id}/lot", headers=header_titik_kumpul)
    assert r.status_code == 200
    lots = r.json()
    assert len(lots) == 4
    lot_by_petani = {lot["nama_petani"]: lot for lot in lots}
    assert all(lot["penerima_id"] is not None for lot in lots)

    # -----------------------------------------------------------------
    # Langkah 8: Muat 4 lot -- timbang + foto. Lot Ijah ditandai cacat
    # terlihat (jadi lot "cacat" untuk langkah 10).
    # -----------------------------------------------------------------
    berat = {"Asep": 298, "Wati": 199, "Dedi": 179, "Ijah": 99}
    for nama, lot in lot_by_petani.items():
        r = client.patch(
            f"/api/lot/{lot['id']}/muat",
            headers=header_titik_kumpul,
            json={
                "berat_aktual_kg": berat[nama],
                "foto_muat_base64": "ZmFrZS1mb3RvLW11YXQ=",
                "grade_asal": 2 if nama == "Ijah" else 5,
                "catatan_muat": "ada memar di beberapa krat" if nama == "Ijah" else "kondisi baik",
            },
        )
        assert r.status_code == 200, r.text
        assert r.json()["berat_aktual_kg"] == berat[nama]
        assert r.json()["foto_muat"] is not None

    r = client.get(f"/api/slot/{slot_id}", headers=header_titik_kumpul)
    assert r.json()["status"] == "DIMUAT"

    r = client.post(f"/api/slot/{slot_id}/selesai-muat", headers=header_titik_kumpul)
    assert r.status_code == 200, r.text
    assert all(lot["waktu_muat"] for lot in r.json())

    r = client.get(f"/api/slot/{slot_id}", headers=header_titik_kumpul)
    assert r.json()["status"] == "JALAN"

    r = client.get(f"/api/slot/{slot_id}/pengiriman", headers=header_titik_kumpul)
    assert r.status_code == 200, r.text
    pengiriman = r.json()
    assert pengiriman["status_vendor"] == "JALAN"
    pengiriman_id = pengiriman["id"]

    # -----------------------------------------------------------------
    # Langkah 9: Lacak -- maju ke TIBA (K5: state simulasi eksplisit).
    # -----------------------------------------------------------------
    r = client.post(f"/api/pengiriman/{pengiriman_id}/majukan", headers=header_titik_kumpul)
    assert r.status_code == 200, r.text
    assert r.json()["status_vendor"] == "TIBA"

    # -----------------------------------------------------------------
    # Langkah 10: Serah terima -- semua lot TERIMA (K14: tidak ada lagi POTONG).
    # Atribusi Ijah wajib PETANI (cacat sudah terlihat sejak muat), sisanya
    # TIDAK_TERBUKTI (tidak ada cacat & transit simulasi jauh di bawah
    # ambang 181 menit karena test berjalan dalam hitungan detik).
    # -----------------------------------------------------------------
    # K13: penerima menemukan kiriman lewat NOMOR RESI, bukan lewat ikatan alamat
    # tetap. Memegang resi = berhak melihat & menyerahterimakan.
    # K14: bukti lot WAJIB membawa indeks mutu -- penerima harus bisa melihat
    # angkanya SEBELUM memutuskan, bukan sesudah.
    for lot in lot_by_petani.values():
        r = client.get(f"/api/lot/qr/{lot['kode_qr']}", headers=header_rina)
        assert r.status_code == 200, r.text
        assert r.json()["lot"]["kode_qr"] == lot["kode_qr"]
        mutu = r.json()["mutu"]
        assert 0 <= mutu["indeks_mutu"] <= 100
        assert mutu["penurunan_mutu_persen"] == 100 - mutu["indeks_mutu"]

    hasil_serah = {}
    for nama, lot in lot_by_petani.items():
        if nama == "Ijah":
            body = {
                "keputusan": "TERIMA",
                "alasan": "Mutu memang sudah di bawah standar saat ditimbang & difoto saat muat.",
                "foto_bongkar_base64": "ZmFrZS1mb3RvLWJvbmdrYXI=",
                "grade_tiba": 2,
            }
        else:
            body = {"keputusan": "TERIMA", "foto_bongkar_base64": "ZmFrZS1mb3RvLWJvbmdrYXI=", "grade_tiba": 3}
        r = client.post(f"/api/lot/{lot['id']}/serah-terima", headers=header_rina, json=body)
        assert r.status_code == 201, r.text
        hasil_serah[nama] = r.json()

    st_ijah = hasil_serah["Ijah"]
    assert st_ijah["keputusan"] == "TERIMA"
    assert st_ijah["atribusi"] == "PETANI"
    assert isinstance(st_ijah["penjelasan"], str) and len(st_ijah["penjelasan"]) > 20
    assert "di bawah standar" in st_ijah["penjelasan"].lower()

    # DoD: "Serah terima menampilkan PENJELASAN atribusi, bukan cuma label" +
    # cabang TIDAK_TERBUKTI wajib teruji (CLAUDE.md #4) -- minimal satu lot
    # TERIMA berujung TIDAK_TERBUKTI.
    lot_tidak_terbukti = [hasil_serah[n] for n in ("Asep", "Wati", "Dedi") if hasil_serah[n]["atribusi"] == "TIDAK_TERBUKTI"]
    assert len(lot_tidak_terbukti) >= 1
    for st in lot_tidak_terbukti:
        assert st["keputusan"] == "TERIMA"
        assert isinstance(st["penjelasan"], str) and len(st["penjelasan"]) > 20
        assert "tidak terekam sistem" in st["penjelasan"].lower()

    r = client.get(f"/api/slot/{slot_id}", headers=header_titik_kumpul)
    assert r.json()["status"] == "SELESAI"

    # -----------------------------------------------------------------
    # Langkah 11: Berita Acara -- rincian ongkos, subsidi, foto muat+bongkar.
    # -----------------------------------------------------------------
    r = client.get(f"/api/slot/{slot_id}/berita-acara", headers=header_titik_kumpul)
    assert r.status_code == 200, r.text
    ba = r.json()
    assert ba["kode_slot"] == slot["kode"]
    assert len(ba["rincian_ongkos"]) == 4
    assert ba["selisih_jaminan_atap"] == -550
    assert ba["harga_final_per_kg"] == 388
    assert len(ba["lot"]) == 4
    for baris in ba["lot"]:
        assert baris["lot"]["foto_muat"] is not None  # K10 sudah tersalur dari langkah 8
        assert baris["serah_terima"] is not None
        assert baris["serah_terima"]["foto_bongkar"] is not None  # K10 amandemen pasca-beku

    # -----------------------------------------------------------------
    # Langkah 12: Dashboard Dampak -- empat kartu semboyan (v2 §7.1) terisi.
    # -----------------------------------------------------------------
    r = client.get("/api/dampak/ringkasan", headers=header_titik_kumpul)
    assert r.status_code == 200, r.text
    ringkasan = r.json()
    # Biaya logistik: Σ(atap×vol − h_i×vol)/Σ(atap×vol) — atap tiap peserta
    # dihitung dari skenario kirim SENDIRI (±1,5–2,4 ribu/kg), jadi penghematan
    # terhadap atap ≈ 73,7% (Σ 845.980 / Σ 1.148.620).
    assert ringkasan["biaya_logistik"]["nilai"] == pytest.approx(73.7, abs=0.1)
    assert "→" in (ringkasan["biaya_logistik"]["sub_teks"] or "")
    # Emisi: (4−1) × 70,03 km × faktor_emisi 0,25 = 52,5225 kg CO₂e.
    assert ringkasan["emisi"]["nilai"] == pytest.approx(52.5225, abs=0.05)
    assert "truk-km tidak jadi ditempuh" in (ringkasan["emisi"]["sub_teks"] or "")
    # Transparansi: durasi terpanjang vs ambang rute 181 menit.
    assert ringkasan["transparansi_perjalanan"]["nilai"] is not None
    assert "181" in (ringkasan["transparansi_perjalanan"]["sub_teks"] or "")
    # Keamanan pangan: sisa umur simpan terisi (telemetri, perjalanan singkat di test).
    assert ringkasan["keamanan_pangan"]["nilai"] == pytest.approx(100, abs=1)

    r = client.get("/api/dampak/bulanan", headers=header_titik_kumpul)
    assert r.status_code == 200
    bulanan = r.json()
    assert len(bulanan) >= 1
    entri_bulan_ini = bulanan[-1]
    assert entri_bulan_ini["jumlah_kiriman"] == 1
    assert entri_bulan_ini["susut_kg"] == pytest.approx(7.8)

    # -----------------------------------------------------------------
    # Langkah 13: Panel Asumsi -- ubah faktor_emisi_kg_co2_per_km, dashboard
    # dampak ikut berubah. Kartu emisi PERSIS berlipat dua (truk-km-nya tidak
    # berubah, hanya faktor pengalinya).
    # -----------------------------------------------------------------
    emisi_awal = ringkasan["emisi"]["nilai"]

    r = client.get("/api/konfigurasi", headers=header_titik_kumpul)
    faktor_emisi_saat_ini = next(k for k in r.json() if k["kunci"] == "faktor_emisi_kg_co2_per_km")
    nilai_baru = float(faktor_emisi_saat_ini["nilai"]) * 2

    r = client.patch(
        "/api/konfigurasi/faktor_emisi_kg_co2_per_km", headers=header_titik_kumpul, json={"nilai": str(nilai_baru)}
    )
    assert r.status_code == 200, r.text
    assert float(r.json()["nilai"]) == pytest.approx(nilai_baru)

    r = client.get("/api/dampak/ringkasan", headers=header_titik_kumpul)
    assert r.status_code == 200
    emisi_baru = r.json()["emisi"]["nilai"]
    assert emisi_baru == pytest.approx(emisi_awal * 2, rel=1e-6)
    # kartu lain (tidak bergantung faktor_emisi) TIDAK ikut berubah -- bukti
    # bahwa perubahan Panel Asumsi terisolasi ke koefisien yang benar-benar
    # relevan, bukan efek samping global.
    assert r.json()["biaya_logistik"]["nilai"] == pytest.approx(73.7, abs=0.1)
    assert r.json()["transparansi_perjalanan"]["sub_teks"] == ringkasan["transparansi_perjalanan"]["sub_teks"]


# ---------------------------------------------------------------------------
# DoD: "Harga atap tidak pernah berubah setelah petani bergabung — diuji,
# bukan diasumsikan." Test terpisah & fokus, tidak bercampur dengan skenario
# demo besar di atas.
# ---------------------------------------------------------------------------


def test_harga_atap_tidak_pernah_berubah_meski_peserta_lain_bergabung(client, data_dasar, masuk, db):
    kubis_id = str(data_dasar["komoditas"]["kubis"].id)

    header_titik_kumpul = masuk("081200000001")
    header_asep = masuk("081200000011")
    header_wati = masuk("081200000012")
    header_dedi = masuk("081200000013")

    slot_id = str(_buat_muatan_3_tujuan(db, data_dasar, kode="SM-ATAP-01").id)

    r = client.post(
        f"/api/slot/{slot_id}/gabung", headers=header_asep, json={"komoditas_id": kubis_id, "volume_kg": 300}
    )
    atap_terkunci = r.json()["harga_atap_per_kg"]
    assert atap_terkunci == 1007

    # Cek berkali-kali SEBELUM ada peserta lain -- baseline.
    for _ in range(2):
        r = client.get(f"/api/slot/{slot_id}", headers=header_asep)
        assert r.json()["atap_saya_per_kg"] == atap_terkunci

    # Wati & Dedi bergabung -> harga berjalan slot pasti berubah (turun),
    # tapi atap Asep, yang sudah dikunci, wajib tetap identik persis.
    for header, volume in ((header_wati, 200), (header_dedi, 180)):
        r_gabung = client.post(
            f"/api/slot/{slot_id}/gabung", headers=header, json={"komoditas_id": kubis_id, "volume_kg": volume}
        )
        assert r_gabung.status_code == 201, r_gabung.text

        r_asep = client.get(f"/api/slot/{slot_id}", headers=header_asep)
        assert r_asep.json()["atap_saya_per_kg"] == atap_terkunci, "atap Asep berubah -- pelanggaran §5.5/CLAUDE.md #3"

    # Sampai penutupan slot: field partisipasi Asep di respons tutup masih
    # membawa harga_atap_per_kg yang identik dengan saat gabung.
    r = client.post(f"/api/slot/{slot_id}/tutup", headers=header_titik_kumpul)
    assert r.status_code == 200, r.text
    partisipasi_asep = next(p for p in r.json()["partisipasi"] if p["nama_petani"] == "Asep")
    assert partisipasi_asep["harga_atap_per_kg"] == atap_terkunci
    # Petani tidak pernah ditagih di atas atapnya (CLAUDE.md #3).
    assert partisipasi_asep["harga_final_per_kg"] <= atap_terkunci


# ---------------------------------------------------------------------------
# DoD: "Dialog LUAPAN_KAPASITAS muncul dan bisa diselesaikan." Isi 1 peserta
# sampai ~800 kg (penuh VAN), lalu +10 kg -> harus 409 dengan body yang
# diperkaya persis sesuai KEPUTUSAN.md K6.
# ---------------------------------------------------------------------------


def test_luapan_kapasitas_409_body_lengkap(client, data_dasar, masuk, db):
    kubis_id = str(data_dasar["komoditas"]["kubis"].id)

    header_titik_kumpul = masuk("081200000001")
    header_asep = masuk("081200000011")
    header_wati = masuk("081200000012")

    slot_row = _buat_muatan_3_tujuan(db, data_dasar, kode="SM-LUAP-01")
    slot_id = str(slot_row.id)
    assert float(slot_row.jarak_km) == pytest.approx(70.03, abs=0.1)

    # Muatan alternatif: DIBUKA, titik kumpul & tanggal sama -> harus muncul di
    # slot_alternatif_id (dua pilihan dialog: "gabung muatan berikutnya").
    slot_alt_id = str(_buat_muatan_3_tujuan(db, data_dasar, kode="SM-LUAP-02").id)

    # Isi ~800 kg (penuh kapasitas VAN pada 70,03 km) dengan Asep sendirian.
    r = client.post(
        f"/api/slot/{slot_id}/gabung", headers=header_asep, json={"komoditas_id": kubis_id, "volume_kg": 800}
    )
    assert r.status_code == 201, r.text
    atap_asep = r.json()["harga_atap_per_kg"]
    assert atap_asep == 378  # 800 kg solo @70,03 km -> VAN 302.090 -> ceil(302090/800)

    # Wati mencoba +10 kg -> 810 kg total wajib pindah ke ENGKEL, H_kasar naik
    # melampaui atap Asep -> 409 LUAPAN_KAPASITAS.
    r = client.post(
        f"/api/slot/{slot_id}/gabung", headers=header_wati, json={"komoditas_id": kubis_id, "volume_kg": 10}
    )
    assert r.status_code == 409, r.text
    body = r.json()  # bentuk APA ADANYA (bukan {"detail": ...}) -- K6
    assert body["kode"] == "LUAPAN_KAPASITAS"
    assert body["harga_baru_per_kg"] == 630  # 810 kg @70,03 km -> ENGKEL 510.099 -> ceil(510099/810)
    assert body["jumlah_atap_terdampak"] == 1
    assert body["slot_alternatif_id"] == slot_alt_id
    assert isinstance(body["pesan"], str) and len(body["pesan"]) > 10

    # Wati belum tercatat -- 409 tidak membuat partisipasi baru.
    r = client.get(f"/api/slot/{slot_id}", headers=header_titik_kumpul)
    assert len(r.json()["partisipasi"]) == 1

    # Dialog "bisa diselesaikan": Wati memilih jalan keluar -- gabung ke slot
    # alternatif yang ditawarkan -- dan itu berhasil normal (201, bukan 409),
    # karena slot alternatif masih kosong.
    r = client.post(
        f"/api/slot/{slot_alt_id}/gabung", headers=header_wati, json={"komoditas_id": kubis_id, "volume_kg": 10}
    )
    assert r.status_code == 201, r.text

    # Pratinjau gabung (peringatan dini sebelum submit, §9.4 butir 5) juga
    # melaporkan luapan yang sama tanpa membuat partisipasi.
    r = client.post(f"/api/slot/{slot_id}/gabung/pratinjau", headers=header_wati, json={"volume_kg": 10})
    assert r.status_code == 200, r.text
    pratinjau_gabung = r.json()
    assert pratinjau_gabung["luapan"] is True
    assert pratinjau_gabung["harga_berjalan_baru_per_kg"] == 630
    assert pratinjau_gabung["pesan"]
