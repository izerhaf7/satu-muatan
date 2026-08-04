"""K14 — autocomplete wilayah & reverse geocoding.

Yang dijaga di sini terutama satu hal: **keduanya jalan tanpa kunci Google dan
tanpa internet.** Demo dibuka juri di jaringan yang tidak bisa kita kendalikan;
alamat tidak boleh berhenti terisi karena layanan luar sedang bermasalah.
"""

import pytest

from app.models import Wilayah


@pytest.fixture()
def wilayah_contoh(db, data_dasar):
    """Beberapa baris wilayah — cukup untuk menguji urutan & pencarian.

    Sengaja TIDAK memuat berkas 6.612 baris: test harus cepat dan hasilnya tidak
    boleh bergantung pada isi dataset yang bisa berubah saat diperbarui."""
    db.add_all(
        [
            Wilayah(
                kode="32.05.22",
                nama="Cikajang",
                tingkat="KECAMATAN",
                induk_kode="32.05",
                jalur="Cikajang, Kabupaten Garut, Jawa Barat",
                lat=-7.3661,
                lng=107.7961,
            ),
            Wilayah(
                kode="32.73.25",
                nama="Cibiru",
                tingkat="KECAMATAN",
                induk_kode="32.73",
                jalur="Cibiru, Kota Bandung, Jawa Barat",
                lat=-6.9269,
                lng=107.7189,
            ),
            Wilayah(
                kode="32.04.12",
                nama="Dayeuhkolot",
                tingkat="KECAMATAN",
                induk_kode="32.04",
                jalur="Dayeuhkolot, Kabupaten Bandung, Jawa Barat",
                lat=-6.98,
                lng=107.62,
            ),
            # Tanpa koordinat — sumber resmi memang tidak menyertakannya.
            Wilayah(
                kode="32.05.22.2001",
                nama="Cikandang",
                tingkat="DESA",
                induk_kode="32.05.22",
                jalur="Cikandang, Cikajang, Kabupaten Garut, Jawa Barat",
            ),
        ]
    )
    db.commit()


def test_autocomplete_menemukan_kecamatan(client, data_dasar, masuk, wilayah_contoh):
    header = masuk("081200000012")
    r = client.get("/api/wilayah/cari", params={"q": "cikaj"}, headers=header)
    assert r.status_code == 200, r.text
    nama = [w["nama"] for w in r.json()]
    assert "Cikajang" in nama


def test_autocomplete_mendahulukan_yang_diawali_kata_kunci(client, data_dasar, masuk, wilayah_contoh):
    """Mengetik "cika" harus memunculkan yang DIAWALI "cika" lebih dulu —
    kalau tidak, daftar terasa acak dan pengguna berhenti mempercayainya."""
    header = masuk("081200000012")
    hasil = client.get("/api/wilayah/cari", params={"q": "cika"}, headers=header).json()
    assert hasil, "seharusnya ada hasil"
    assert all(w["nama"].lower().startswith("cika") for w in hasil[:2])


def test_autocomplete_membawa_jalur_dan_koordinat(client, data_dasar, masuk, wilayah_contoh):
    header = masuk("081200000012")
    hasil = client.get("/api/wilayah/cari", params={"q": "cibiru"}, headers=header).json()
    cibiru = next(w for w in hasil if w["nama"] == "Cibiru")
    assert cibiru["jalur"] == "Cibiru, Kota Bandung, Jawa Barat"
    assert cibiru["lat"] == pytest.approx(-6.9269)


def test_autocomplete_menolak_kata_kunci_terlalu_pendek(client, data_dasar, masuk, wilayah_contoh):
    header = masuk("081200000012")
    assert client.get("/api/wilayah/cari", params={"q": "c"}, headers=header).status_code == 422


def test_geokode_balik_jalan_tanpa_kunci_google(client, data_dasar, masuk, wilayah_contoh):
    """Inti keputusan arsitektur: tanpa GOOGLE_MAPS_API_KEY pun alamat terisi."""
    header = masuk("081200000012")
    r = client.get("/api/geokode/balik", params={"lat": -6.9269, "lng": 107.7189}, headers=header)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sumber"] == "LOKAL"
    assert body["kecamatan"] == "Cibiru"
    assert body["kabupaten"] == "Kota Bandung"


def test_geokode_balik_memilih_wilayah_terdekat(client, data_dasar, masuk, wilayah_contoh):
    header = masuk("081200000012")
    r = client.get("/api/geokode/balik", params={"lat": -7.3661, "lng": 107.7961}, headers=header)
    assert r.json()["kecamatan"] == "Cikajang"


def test_geokode_balik_di_cache_dan_tidak_dihitung_ulang(client, data_dasar, masuk, wilayah_contoh, db):
    """Titik yang sama diketuk berulang kali tidak boleh memanggil jaringan lagi."""
    from app.models import GeokodeCache

    header = masuk("081200000012")
    params = {"lat": -6.98, "lng": 107.62}
    pertama = client.get("/api/geokode/balik", params=params, headers=header).json()
    assert db.query(GeokodeCache).count() == 1

    kedua = client.get("/api/geokode/balik", params=params, headers=header).json()
    assert kedua == pertama
    assert db.query(GeokodeCache).count() == 1, "permintaan kedua seharusnya dilayani cache"


def test_geokode_balik_tanpa_data_wilayah_tetap_menjawab(client, data_dasar, masuk):
    """Tabel wilayah kosong (mis. berkas seed belum diunduh) bukan alasan gagal."""
    header = masuk("081200000012")
    r = client.get("/api/geokode/balik", params={"lat": -6.9, "lng": 107.6}, headers=header)
    assert r.status_code == 200, r.text
    assert r.json()["sumber"] == "LOKAL"
    assert r.json()["alamat"]
