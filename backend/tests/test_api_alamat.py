"""K14 — autocomplete wilayah & reverse geocoding.

Yang dijaga di sini terutama satu hal: **keduanya jalan tanpa kunci Google dan
tanpa internet.** Demo dibuka juri di jaringan yang tidak bisa kita kendalikan;
alamat tidak boleh berhenti terisi karena layanan luar sedang bermasalah.
"""

import json
from pathlib import Path

import pytest
import yaml

from app.adapters.geo.base import AddressResult, CoordinateResult, SuggestionResult
from app.adapters.geo.google import GoogleGeoAdapter
from app.adapters.geo.local import LocalGeoAdapter
from app.services.geokode import geokode_balik
from app.models import GeokodeCache, Wilayah


def test_schema_alamat_runtime_persis_kontrak_beku():
    from app.main import app

    kontrak = yaml.safe_load(
        (Path(__file__).resolve().parents[2] / "kontrak" / "openapi.yaml").read_text(encoding="utf-8")
    )
    runtime = app.openapi()
    nama_schema = [
        "AlamatSaranBias",
        "AlamatSaranRequest",
        "AlamatSaranItemOut",
        "AlamatSaranListOut",
        "AlamatResolusiRequest",
        "AlamatResolusiOut",
        "GranularitasAlamat",
        "StatusResolusiAlamat",
        "StatusSaranAlamat",
        "SumberAlamat",
    ]
    assert {name: runtime["components"]["schemas"][name] for name in nama_schema} == {
        name: kontrak["components"]["schemas"][name] for name in nama_schema
    }


def test_operasi_alamat_runtime_persis_kontrak_beku():
    from app.main import app

    kontrak = yaml.safe_load(
        (Path(__file__).resolve().parents[2] / "kontrak" / "openapi.yaml").read_text(encoding="utf-8")
    )
    runtime = app.openapi()

    for path in ("/api/alamat/saran", "/api/alamat/resolusi"):
        assert runtime["paths"][path]["post"] == kontrak["paths"][path]["post"]


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
                kode="32.73",
                nama="Kota Bandung",
                tingkat="KABUPATEN",
                induk_kode="32",
                jalur="Kota Bandung, Jawa Barat",
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
            Wilayah(
                kode="32.05.22.2002",
                nama="Mekarsari",
                tingkat="DESA",
                induk_kode="32.05.22",
                jalur="Mekarsari, Cikajang, Kabupaten Garut, Jawa Barat",
                kode_pos="44171",
                lat=-7.37,
                lng=107.80,
            ),
            Wilayah(
                kode="32",
                nama="Jawa Barat",
                tingkat="PROVINSI",
                jalur="Jawa Barat",
            ),
            Wilayah(
                kode="32.05",
                nama="Kabupaten Garut",
                tingkat="KABUPATEN",
                induk_kode="32",
                jalur="Kabupaten Garut, Jawa Barat",
                lat=-7.20,
                lng=107.90,
            ),
            Wilayah(
                kode="32.05.01",
                nama="A Kecamatan",
                tingkat="KECAMATAN",
                induk_kode="32.05",
                jalur="A Kecamatan, Kabupaten Garut, Jawa Barat",
            ),
            Wilayah(
                kode="32.05.02",
                nama="B Kecamatan",
                tingkat="KECAMATAN",
                induk_kode="32.05",
                jalur="B Kecamatan, Kabupaten Garut, Jawa Barat",
            ),
        ]
    )
    db.commit()


def test_wilayah_anak_memerlukan_autentikasi(client, data_dasar, wilayah_contoh):
    r = client.get("/api/wilayah/anak", params={"tingkat": "PROVINSI"})
    assert r.status_code == 401


def test_wilayah_anak_menolak_tingkat_tidak_valid(client, data_dasar, masuk, wilayah_contoh):
    header = masuk("081200000012")
    r = client.get(
        "/api/wilayah/anak",
        params={"tingkat": "KOTA", "induk_kode": "32"},
        headers=header,
    )
    assert r.status_code == 422


def test_wilayah_anak_provinsi_tanpa_induk_dan_urut_nama(client, data_dasar, masuk, wilayah_contoh):
    header = masuk("081200000012")
    r = client.get("/api/wilayah/anak", params={"tingkat": "PROVINSI"}, headers=header)
    assert r.status_code == 200, r.text
    assert r.json() == [
        {
            "kode": "32",
            "nama": "Jawa Barat",
            "tingkat": "PROVINSI",
            "jalur": "Jawa Barat",
            "kode_pos": None,
            "lat": None,
            "lng": None,
            "induk_kode": None,
        }
    ]


@pytest.mark.parametrize("tingkat", ["KABUPATEN", "KECAMATAN", "DESA"])
def test_wilayah_anak_tingkat_selain_provinsi_memerlukan_induk(
    client, data_dasar, masuk, wilayah_contoh, tingkat
):
    header = masuk("081200000012")
    r = client.get("/api/wilayah/anak", params={"tingkat": tingkat}, headers=header)
    assert r.status_code == 422


@pytest.mark.parametrize("induk_kode", ["", "   ", "\t"])
@pytest.mark.parametrize("tingkat", ["KABUPATEN", "KECAMATAN", "DESA"])
def test_wilayah_anak_menolak_induk_kosong_untuk_tingkat_selain_provinsi(
    client, data_dasar, masuk, wilayah_contoh, tingkat, induk_kode
):
    header = masuk("081200000012")
    r = client.get(
        "/api/wilayah/anak",
        params={"tingkat": tingkat, "induk_kode": induk_kode},
        headers=header,
    )
    assert r.status_code == 422


def test_wilayah_anak_provinsi_menolak_induk_yang_disuplai(client, data_dasar, masuk, wilayah_contoh):
    header = masuk("081200000012")
    r = client.get(
        "/api/wilayah/anak",
        params={"tingkat": "PROVINSI", "induk_kode": "32"},
        headers=header,
    )
    assert r.status_code == 422


def test_wilayah_anak_memfilter_tingkat_dan_induk_lalu_urut_nama(client, data_dasar, masuk, wilayah_contoh):
    header = masuk("081200000012")
    r = client.get(
        "/api/wilayah/anak",
        params={"tingkat": "KECAMATAN", "induk_kode": "32.05"},
        headers=header,
    )
    assert r.status_code == 200, r.text
    hasil = r.json()
    assert [w["nama"] for w in hasil] == ["A Kecamatan", "B Kecamatan", "Cikajang"]
    assert all(w["tingkat"] == "KECAMATAN" and w["induk_kode"] == "32.05" for w in hasil)


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
    assert body["jarak_meter"] == pytest.approx(0)
    assert body["keyakinan"] == pytest.approx(1)


def test_geokode_balik_metadata_lokal_memakai_jarak_dan_formula_keyakinan(
    client, data_dasar, masuk, wilayah_contoh
):
    """keyakinan = clamp(1 - jarak_meter / (maks_km * 1000), 0, 1)."""
    header = masuk("081200000012")
    lat = -6.9369
    lng = 107.7189

    body = client.get("/api/geokode/balik", params={"lat": lat, "lng": lng}, headers=header).json()
    jarak_meter = body["jarak_meter"]

    assert jarak_meter > 0
    assert body["keyakinan"] == pytest.approx(max(0, min(1, 1 - jarak_meter / 25_000)))


def test_geokode_balik_memilih_wilayah_terdekat(client, data_dasar, masuk, wilayah_contoh):
    header = masuk("081200000012")
    r = client.get("/api/geokode/balik", params={"lat": -7.3661, "lng": 107.7961}, headers=header)
    assert r.json()["kecamatan"] == "Cikajang"


def test_local_reverse_mengikuti_hierarki_induk_desa(db, wilayah_contoh):
    hasil = LocalGeoAdapter(db, max_distance_km=10).reverse(-7.37, 107.80)
    assert hasil == AddressResult(
        alamat="Mekarsari, Cikajang, Kabupaten Garut, Jawa Barat",
        desa="Mekarsari",
        kecamatan="Cikajang",
        kabupaten="Kabupaten Garut",
        provinsi="Jawa Barat",
        kode_pos="44171",
        sumber="LOKAL",
        jarak_meter=0,
        keyakinan=1,
    )


def test_local_reverse_mengikuti_hierarki_induk_kecamatan(db, wilayah_contoh):
    hasil = LocalGeoAdapter(db, max_distance_km=10).reverse(-6.9269, 107.7189)
    assert hasil.desa is None
    assert hasil.kecamatan == "Cibiru"
    assert hasil.kabupaten == "Kota Bandung"
    assert hasil.provinsi == "Jawa Barat"


def test_local_reverse_mengikuti_hierarki_induk_kabupaten(db, wilayah_contoh):
    hasil = LocalGeoAdapter(db, max_distance_km=10).reverse(-7.20, 107.90)
    assert hasil.desa is None
    assert hasil.kecamatan is None
    assert hasil.kabupaten == "Kabupaten Garut"
    assert hasil.provinsi == "Jawa Barat"


def test_local_reverse_hierarki_sparse_tidak_menebak_dari_jalur(db, wilayah_contoh):
    db.add(
        Wilayah(
            kode="99.99.99",
            nama="Wilayah Tanpa Induk",
            tingkat="KECAMATAN",
            induk_kode="99.99",
            jalur="Wilayah Tanpa Induk, Soreang, Kabupaten Bandung, Jawa Barat",
            lat=-8.0,
            lng=108.0,
        )
    )
    db.commit()

    hasil = LocalGeoAdapter(db, max_distance_km=10).reverse(-8.0, 108.0)
    assert hasil.sumber == "TIDAK_DITEMUKAN"
    assert hasil.alamat == "Titik -8.0000, 108.0000"
    assert hasil.kecamatan is None
    assert hasil.kabupaten is None
    assert hasil.provinsi is None


def test_local_reverse_hierarki_salah_urut_tidak_diterima(db, wilayah_contoh):
    db.add_all(
        [
            Wilayah(
                kode="98.01",
                nama="Kabupaten Silang",
                tingkat="KABUPATEN",
                induk_kode="98.01.01",
                jalur="Kabupaten Silang",
            ),
            Wilayah(
                kode="98.01.01",
                nama="Kecamatan Silang",
                tingkat="KECAMATAN",
                induk_kode="32",
                jalur="Kecamatan Silang, Kabupaten Silang, Jawa Barat",
            ),
            Wilayah(
                kode="98.01.01.0001",
                nama="Desa Silang",
                tingkat="DESA",
                induk_kode="98.01",
                jalur="Desa Silang, Kecamatan Silang, Kabupaten Silang, Jawa Barat",
                lat=-8.1,
                lng=108.1,
            ),
        ]
    )
    db.commit()

    hasil = LocalGeoAdapter(db, max_distance_km=10).reverse(-8.1, 108.1)
    assert hasil.sumber == "TIDAK_DITEMUKAN"
    assert hasil.desa is None


def test_local_reverse_radius_non_finite_gagal_aman(db, wilayah_contoh):
    hasil = LocalGeoAdapter(db, max_distance_km=float("nan")).reverse(-6.2, 106.8)
    assert hasil.sumber == "TIDAK_DITEMUKAN"


def test_geokode_balik_titik_jauh_tidak_memakai_centroid_terdekat(
    client, data_dasar, masuk, wilayah_contoh
):
    header = masuk("081200000012")
    r = client.get("/api/geokode/balik", params={"lat": -6.2, "lng": 106.8}, headers=header)
    assert r.status_code == 200, r.text
    assert r.json() == {
        "alamat": "Titik -6.2000, 106.8000",
        "desa": None,
        "kecamatan": None,
        "kabupaten": None,
        "provinsi": None,
        "kode_pos": None,
        "sumber": "TIDAK_DITEMUKAN",
        "jarak_meter": None,
        "keyakinan": None,
    }


def test_geokode_balik_mengabaikan_cache_algoritma_lama(db, wilayah_contoh, monkeypatch):
    from app.services import geokode

    db.add(
        GeokodeCache(
            kunci="-6.2,106.8",
            sumber="LOKAL",
            hasil_json=json.dumps(
                {
                    "alamat": "Soreang, Kabupaten Bandung, Jawa Barat",
                    "kecamatan": "Soreang",
                    "kabupaten": "Kabupaten Bandung",
                    "provinsi": "Jawa Barat",
                    "sumber": "LOKAL",
                }
            ),
        )
    )
    db.commit()
    monkeypatch.setattr(geokode, "_google_provider", lambda settings: None)

    hasil = geokode_balik(db, -6.2, 106.8)

    assert hasil.sumber == "TIDAK_DITEMUKAN"
    assert hasil.alamat == "Titik -6.2000, 106.8000"


def test_cache_lokal_tidak_menghalangi_google_yang_baru_diaktifkan(db, wilayah_contoh, monkeypatch):
    from types import SimpleNamespace

    from app.services import geokode

    tanpa_google = SimpleNamespace(
        geo_provider_enabled=False,
        google_maps_api_key="",
        geo_local_max_distance_km=25,
    )
    dengan_google = SimpleNamespace(
        geo_provider_enabled=True,
        google_maps_api_key="key",
        geo_local_max_distance_km=25,
    )
    settings = tanpa_google
    calls = []

    class Provider:
        def reverse(self, lat, lng):
            calls.append((lat, lng))
            return AddressResult(alamat="Alamat Google baru", sumber="GOOGLE")

    monkeypatch.setattr(geokode, "get_settings", lambda: settings)
    monkeypatch.setattr(geokode, "GoogleGeoAdapter", lambda key: Provider())

    pertama = geokode_balik(db, -6.9269, 107.7189)
    settings = dengan_google
    kedua = geokode_balik(db, -6.9269, 107.7189)

    assert pertama.sumber == "LOKAL"
    assert kedua == AddressResult(alamat="Alamat Google baru", sumber="GOOGLE")
    assert calls == [(-6.9269, 107.7189)]
    assert db.query(GeokodeCache).count() == 2


def test_cache_memakai_satu_snapshot_konfigurasi_provider_per_request(db, wilayah_contoh, monkeypatch):
    """Perubahan config di tengah request tidak boleh memilih key lokal yang stale."""
    from types import SimpleNamespace

    from app.services import geokode

    tanpa_google = SimpleNamespace(
        geo_provider_enabled=False,
        google_maps_api_key="",
        geo_local_max_distance_km=25,
    )
    dengan_google = SimpleNamespace(
        geo_provider_enabled=True,
        google_maps_api_key="key",
        geo_local_max_distance_km=25,
    )
    settings = [tanpa_google, dengan_google]
    calls = []

    class Provider:
        def reverse(self, lat, lng):
            calls.append((lat, lng))
            return AddressResult(alamat="Google dari snapshot aktif", sumber="GOOGLE")

    monkeypatch.setattr(geokode, "get_settings", lambda: settings.pop(0))
    monkeypatch.setattr(geokode, "GoogleGeoAdapter", lambda key: Provider())

    pertama = geokode_balik(db, -6.9269, 107.7189)
    kedua = geokode_balik(db, -6.9269, 107.7189)

    assert pertama.sumber == "LOKAL"
    assert kedua.alamat == "Google dari snapshot aktif"
    assert calls == [(-6.9269, 107.7189)]
    assert settings == []


def test_cache_google_tidak_dipakai_setelah_provider_dinonaktifkan(db, wilayah_contoh, monkeypatch):
    from types import SimpleNamespace

    from app.services import geokode

    dengan_google = SimpleNamespace(
        geo_provider_enabled=True,
        google_maps_api_key="key",
        geo_local_max_distance_km=25,
    )
    tanpa_google = SimpleNamespace(
        geo_provider_enabled=False,
        google_maps_api_key="key",
        geo_local_max_distance_km=25,
    )
    settings = dengan_google

    class Provider:
        def reverse(self, lat, lng):
            return AddressResult(alamat="Alamat Google lama", sumber="GOOGLE")

    monkeypatch.setattr(geokode, "get_settings", lambda: settings)
    monkeypatch.setattr(geokode, "GoogleGeoAdapter", lambda key: Provider())

    pertama = geokode_balik(db, -6.9269, 107.7189)
    settings = tanpa_google
    kedua = geokode_balik(db, -6.9269, 107.7189)

    assert pertama.sumber == "GOOGLE"
    assert kedua.sumber == "LOKAL"
    assert kedua.alamat != pertama.alamat


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
    assert r.json()["sumber"] == "TIDAK_DITEMUKAN"
    assert r.json()["alamat"]


def test_geo_result_types_immutable():
    hasil = AddressResult(alamat="Cikajang", sumber="LOKAL")
    with pytest.raises(AttributeError):
        setattr(hasil, "alamat", "Lain")


def test_local_adapter_menyediakan_autocomplete_dan_forward(db, wilayah_contoh):
    adapter = LocalGeoAdapter(db, max_distance_km=25)
    saran = adapter.autocomplete("cika", 10)
    assert isinstance(saran[0], SuggestionResult)
    assert saran[0].nama == "Cikajang"

    koordinat = adapter.forward("Cikajang")
    assert isinstance(koordinat, CoordinateResult)
    assert koordinat.lat == pytest.approx(-7.3661)


def test_google_adapter_memakai_field_mask_dan_memetakan_respons(monkeypatch):
    calls = []

    def fake_request(url, timeout, headers=None):
        calls.append((url, timeout, headers or {}))
        return {
            "results": [
                {
                    "formattedAddress": "Cikajang, Indonesia",
                    "addressComponents": [
                        {"longText": "Cikajang", "types": ["administrative_area_level_3"]},
                        {"longText": "Garut", "types": ["administrative_area_level_2"]},
                    ],
                }
            ]
        }

    adapter = GoogleGeoAdapter("secret", request_json=fake_request)
    hasil = adapter.reverse(-7.3, 107.7)
    assert hasil is not None
    assert hasil == AddressResult(
        alamat="Cikajang, Indonesia",
        kecamatan="Cikajang",
        kabupaten="Garut",
        sumber="GOOGLE",
    )
    assert hasil.jarak_meter is None
    assert hasil.keyakinan is None
    assert calls[0][0] == "https://geocode.googleapis.com/v4/geocode/location/-7.3,107.7?languageCode=id"
    assert calls[0][1] <= 5
    assert calls[0][2]["X-Goog-Api-Key"] == "secret"
    assert calls[0][2]["X-Goog-FieldMask"] == "results.formattedAddress,results.addressComponents"
    assert "secret" not in calls[0][0]


def test_google_adapter_forward_dan_autocomplete_memetakan_respons():
    calls = []

    def fake_request(url, timeout, headers=None, method="GET", body=None):
        calls.append((url, timeout, headers or {}, method, body))
        if "/v4/geocode/address/" in url:
            return {
                "results": [
                    {
                        "location": {"latitude": -7.3, "longitude": 107.7},
                        "formattedAddress": "Cikajang, Indonesia",
                    }
                ]
            }
        return {
            "suggestions": [
                {
                    "placePrediction": {
                        "placeId": "abc",
                        "text": {"text": "Cikajang, Garut"},
                    }
                }
            ]
        }

    adapter = GoogleGeoAdapter("secret", request_json=fake_request)
    koordinat = adapter.forward("Cikajang, Garut")
    assert koordinat is not None
    assert koordinat.lat == pytest.approx(-7.3)
    forward_call = calls[-1]
    assert forward_call[0] == "https://geocode.googleapis.com/v4/geocode/address/Cikajang%2C%20Garut?languageCode=id"
    assert forward_call[1] <= 5
    assert forward_call[2]["X-Goog-Api-Key"] == "secret"
    assert forward_call[2]["X-Goog-FieldMask"] == "results.location,results.formattedAddress"
    assert "secret" not in forward_call[0]
    assert adapter.autocomplete("cika", 5)[0].place_id == "abc"
    autocomplete_call = calls[-1]
    assert autocomplete_call[0] == "https://places.googleapis.com/v1/places:autocomplete"
    assert autocomplete_call[3] == "POST"
    assert autocomplete_call[2]["Content-Type"] == "application/json"
    assert autocomplete_call[2]["X-Goog-Api-Key"] == "secret"
    assert "X-Goog-FieldMask" in autocomplete_call[2]
    assert json.loads(autocomplete_call[4].decode("utf-8")) == {
        "input": "cika",
        "includedRegionCodes": ["id"],
        "languageCode": "id",
        "regionCode": "id",
        "includeQueryPredictions": False,
    }


def test_google_adapter_meneruskan_http_error_geocoding_v4():
    from email.message import Message
    from urllib.error import HTTPError

    def failing_request(url, timeout, headers=None):
        raise HTTPError(url, 503, "unavailable", Message(), None)

    adapter = GoogleGeoAdapter("secret", request_json=failing_request)
    with pytest.raises(HTTPError):
        adapter.reverse(-7.3, 107.7)


def test_geokode_balik_fallback_saat_provider_enabled_timeout(monkeypatch, db, wilayah_contoh):
    from app.services import geokode

    class TimeoutProvider:
        def reverse(self, lat, lng):
            raise TimeoutError("provider timeout")

    monkeypatch.setattr(geokode, "_google_provider", lambda settings: TimeoutProvider())
    hasil = geokode_balik(db, -6.9269, 107.7189)
    assert hasil.sumber == "LOKAL"
    assert hasil.kecamatan == "Cibiru"


def test_geokode_balik_provider_disabled_does_not_call_google(monkeypatch, db, wilayah_contoh):
    from types import SimpleNamespace
    from app.services import geokode

    calls = []
    monkeypatch.setattr(geokode, "get_settings", lambda: SimpleNamespace(geo_provider_enabled=False, google_maps_api_key="key", geo_local_max_distance_km=25))
    monkeypatch.setattr(geokode, "GoogleGeoAdapter", lambda key: calls.append(key))
    hasil = geokode_balik(db, -6.9269, 107.7189)
    assert hasil.sumber == "LOKAL"
    assert calls == []


def test_geokode_balik_tanpa_kunci_tidak_memanggil_google(monkeypatch, db, wilayah_contoh):
    from types import SimpleNamespace
    from app.services import geokode

    calls = []
    monkeypatch.setattr(geokode, "get_settings", lambda: SimpleNamespace(geo_provider_enabled=True, google_maps_api_key="", geo_local_max_distance_km=25))
    monkeypatch.setattr(geokode, "GoogleGeoAdapter", lambda key: calls.append(key))
    hasil = geokode_balik(db, -6.9269, 107.7189)
    assert hasil.sumber == "LOKAL"
    assert calls == []


def test_geokode_balik_fallback_saat_google_exception(monkeypatch, db, wilayah_contoh):
    from app.services import geokode

    monkeypatch.setattr(
        geokode,
        "_google_provider",
        lambda settings: (_ for _ in ()).throw(RuntimeError("down")),
    )
    hasil = geokode_balik(db, -6.9269, 107.7189)
    assert hasil.sumber == "LOKAL"
    assert hasil.kecamatan == "Cibiru"


def test_geokode_balik_konflik_cache_membaca_pemenang_dan_memulihkan_sesi(monkeypatch, db, wilayah_contoh):
    from sqlalchemy.exc import IntegrityError

    from app.models import GeokodeCache
    from app.services import geokode

    monkeypatch.setattr(geokode, "_google_provider", lambda settings: None)
    commit_asli = db.commit
    rollback_asli = db.rollback
    konflik = True

    def commit_dengan_pemenang():
        nonlocal konflik
        if konflik:
            konflik = False
            raise IntegrityError("insert", {}, Exception("duplicate key"))
        commit_asli()

    def rollback_dengan_pemenang():
        rollback_asli()
        db.add(
            GeokodeCache(
                kunci="reverse-v3:lokal-v2:-6.9269,107.7189",
                sumber="GOOGLE",
                hasil_json=json.dumps({"alamat": "Pemenang", "sumber": "GOOGLE"}),
            )
        )
        commit_asli()

    monkeypatch.setattr(db, "commit", commit_dengan_pemenang)
    monkeypatch.setattr(db, "rollback", rollback_dengan_pemenang)
    hasil = geokode_balik(db, -6.9269, 107.7189)
    assert hasil.alamat == "Pemenang"
    assert hasil.sumber == "GOOGLE"
    assert db.query(GeokodeCache).count() == 1


def test_geokode_balik_google_gagal_tidak_dicache_dan_request_berikutnya_mencoba_lagi(
    monkeypatch, db, wilayah_contoh
):
    from types import SimpleNamespace

    from app.adapters.geo.base import AddressResult
    from app.services import geokode

    class FlakyProvider:
        def __init__(self):
            self.calls = 0

        def reverse(self, lat, lng):
            self.calls += 1
            if self.calls == 1:
                raise TimeoutError("provider timeout")
            return AddressResult(alamat="Google berhasil", sumber="GOOGLE")

    provider = FlakyProvider()
    monkeypatch.setattr(geokode, "get_settings", lambda: SimpleNamespace(geo_provider_enabled=True, google_maps_api_key="key", geo_local_max_distance_km=25))
    monkeypatch.setattr(geokode, "_google_provider", lambda settings: provider)

    pertama = geokode_balik(db, -6.9269, 107.7189)
    assert pertama.sumber == "LOKAL"
    assert db.query(geokode.GeokodeCache).count() == 0

    kedua = geokode_balik(db, -6.9269, 107.7189)
    assert kedua.alamat == "Google berhasil"
    assert kedua.sumber == "GOOGLE"
    assert provider.calls == 2
    assert db.query(geokode.GeokodeCache).count() == 1


def test_saran_alamat_memerlukan_autentikasi(client, data_dasar):
    assert client.post("/api/alamat/saran", json={"query": "Cibiru"}).status_code == 401


@pytest.mark.parametrize("query", ["ab", "x" * 201])
def test_saran_alamat_menegakkan_panjang_query_3_sampai_200(client, data_dasar, masuk, query):
    response = client.post(
        "/api/alamat/saran",
        json={"query": query},
        headers=masuk("081200000012"),
    )
    assert response.status_code == 422


def test_saran_alamat_fallback_lokal_deterministik_maksimal_lima_dan_token_opaque(
    client, data_dasar, masuk, wilayah_contoh, monkeypatch
):
    from types import SimpleNamespace
    from app.services import alamat_saran

    monkeypatch.setattr(
        alamat_saran,
        "get_settings",
        lambda: SimpleNamespace(
            geo_provider_enabled=False,
            google_maps_api_key="",
            geo_local_max_distance_km=25,
            alamat_saran_max_hasil=5,
            alamat_bias_radius_max_meter=20_000,
            jwt_secret="rahasia-token-lokal",
        ),
    )
    header = masuk("081200000012")
    pertama = client.post("/api/alamat/saran", json={"query": "kecamatan"}, headers=header)
    kedua = client.post("/api/alamat/saran", json={"query": "kecamatan"}, headers=header)

    assert pertama.status_code == 200, pertama.text
    assert pertama.json() == kedua.json()
    assert pertama.json()["status"] == "FALLBACK_LOKAL"
    assert len(pertama.json()["saran"]) <= 5
    assert all(item["sumber"] == "LOKAL" for item in pertama.json()["saran"])
    assert all("32." not in item["place_id"] for item in pertama.json()["saran"])
    assert all(item["place_id"].replace(".", "").replace("_", "").replace("~", "").replace("-", "").isalnum() for item in pertama.json()["saran"])


def test_google_autocomplete_memaksa_indonesia_mask_sempit_bias_dan_batas_lima():
    calls = []

    def fake_request(url, timeout, headers=None, method="GET", body=None):
        assert body is not None
        calls.append((url, timeout, headers, method, json.loads(body)))
        return {
            "suggestions": [
                {
                    "placePrediction": {
                        "placeId": f"place-{i}",
                        "text": {"text": f"Alamat lengkap {i}"},
                        "structuredFormat": {
                            "mainText": {"text": f"Alamat {i}"},
                            "secondaryText": {"text": "Jawa Barat, Indonesia"},
                        },
                    }
                }
                for i in range(7)
            ] + [{"queryPrediction": {"text": {"text": "abaikan"}}}]
        }

    adapter = GoogleGeoAdapter("sangat-rahasia", timeout=3.25, request_json=fake_request)
    hasil = adapter.autocomplete("x" * 250, 99, bias=(-6.9, 107.6, 999_999), max_input=200, max_radius=12_000)

    assert len(hasil) == 5
    assert hasil[0].nama == "Alamat 0"
    assert hasil[0].alamat == "Alamat lengkap 0"
    url, timeout, headers, method, body = calls[0]
    assert url == "https://places.googleapis.com/v1/places:autocomplete"
    assert timeout == 3.25
    assert method == "POST"
    assert headers == {
        "X-Goog-Api-Key": "sangat-rahasia",
        "X-Goog-FieldMask": (
            "suggestions.placePrediction.placeId,suggestions.placePrediction.text.text,"
            "suggestions.placePrediction.structuredFormat.mainText.text,"
            "suggestions.placePrediction.structuredFormat.secondaryText.text"
        ),
        "Content-Type": "application/json",
    }
    assert body == {
        "input": "x" * 200,
        "includedRegionCodes": ["id"],
        "languageCode": "id",
        "regionCode": "id",
        "includeQueryPredictions": False,
        "locationBias": {
            "circle": {
                "center": {"latitude": -6.9, "longitude": 107.6},
                "radius": 12_000,
            }
        },
    }
    assert "sangat-rahasia" not in url


def test_google_resolusi_memakai_v4_place_mask_server_dan_normalisasi_berdasarkan_types():
    calls = []

    def fake_request(url, timeout, headers=None):
        calls.append((url, timeout, headers))
        return {
            "formattedAddress": "Jl. Melati 7, Cibiru, Kota Bandung, Jawa Barat 40614, Indonesia",
            "addressComponents": [
                {"longText": "Jawa Barat", "types": ["administrative_area_level_1"]},
                {"longText": "40614", "types": ["postal_code"]},
                {"longText": "7", "types": ["street_number"]},
                {"longText": "Melati", "types": ["route"]},
                {"longText": "Kota Bandung", "types": ["administrative_area_level_2"]},
                {"longText": "Cibiru", "types": ["administrative_area_level_3"]},
                {"longText": "Palasari", "types": ["administrative_area_level_4"]},
            ],
            "location": {"latitude": -6.91, "longitude": 107.72},
            "granularity": "ROOFTOP",
            "placeId": "abc_123",
        }

    adapter = GoogleGeoAdapter("secret", timeout=2.5, request_json=fake_request)
    hasil = adapter.resolve_place("abc_123")

    assert hasil.alamat == "Jl. Melati 7, Cibiru, Kota Bandung, Jawa Barat 40614, Indonesia"
    assert hasil.jalan == "Melati 7"
    assert hasil.kode_pos == "40614"
    assert hasil.desa == "Palasari"
    assert hasil.kecamatan == "Cibiru"
    assert hasil.kabupaten == "Kota Bandung"
    assert hasil.provinsi == "Jawa Barat"
    assert hasil.lat == pytest.approx(-6.91)
    assert hasil.lng == pytest.approx(107.72)
    assert hasil.granularitas == "ALAMAT"
    assert hasil.koordinat_presisi is True
    assert hasil.sumber == "GOOGLE"
    assert calls == [
        (
            "https://geocode.googleapis.com/v4/geocode/places/abc_123?languageCode=id&regionCode=ID",
            2.5,
            {
                "X-Goog-Api-Key": "secret",
                "X-Goog-FieldMask": "formattedAddress,addressComponents,location,granularity,placeId",
            },
        )
    ]


@pytest.mark.parametrize(
    ("granularity", "normalized", "presisi"),
    [
        ("ROOFTOP", "ALAMAT", True),
        ("RANGE_INTERPOLATED", "JALAN", False),
        ("GEOMETRIC_CENTER", None, False),
        ("APPROXIMATE", None, False),
        ("LOCALITY", None, False),
        ("ADMINISTRATIVE_AREA", None, False),
        ("NILAI_BARU_TIDAK_DIKENAL", None, False),
    ],
)
def test_google_resolusi_granularitas_dinormalisasi_dengan_allowlist_konservatif(
    granularity, normalized, presisi
):
    adapter = GoogleGeoAdapter(
        "secret",
        request_json=lambda *args: {
            "formattedAddress": "Alamat hasil penyedia",
            "addressComponents": [],
            "location": {"latitude": -6.9, "longitude": 107.6},
            "granularity": granularity,
            "placeId": "abc",
        },
    )

    hasil = adapter.resolve_place("abc")

    assert hasil.granularitas == normalized
    assert hasil.koordinat_presisi is presisi


@pytest.mark.parametrize("granularity", ["RANGE_INTERPOLATED", "GEOMETRIC_CENTER", "APPROXIMATE", "LOCALITY", "NILAI_BARU"])
def test_api_resolusi_google_granularitas_nonpresisi_meminta_konfirmasi_peta(
    client, data_dasar, masuk, monkeypatch, granularity
):
    from types import SimpleNamespace
    from app.services import alamat_saran

    class Provider:
        def resolve_place(self, place_id):
            adapter = GoogleGeoAdapter(
                "secret",
                request_json=lambda *args: {
                    "formattedAddress": "Alamat kasar tetapi berguna",
                    "addressComponents": [],
                    "location": {"latitude": -6.9, "longitude": 107.6},
                    "granularity": granularity,
                    "placeId": place_id,
                },
            )
            return adapter.resolve_place(place_id)

    monkeypatch.setattr(
        alamat_saran,
        "get_settings",
        lambda: SimpleNamespace(
            geo_provider_enabled=True,
            google_maps_api_key="SECRET",
            geo_local_max_distance_km=25,
            alamat_provider_timeout_detik=3,
            alamat_provider_response_max_bytes=32_768,
            jwt_secret="rahasia-token-lokal",
        ),
    )
    monkeypatch.setattr(alamat_saran, "GoogleGeoAdapter", lambda *args, **kwargs: Provider())

    response = client.post(
        "/api/alamat/resolusi",
        json={"place_id": "abc"},
        headers=masuk("081200000012"),
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "KOORDINAT_TIDAK_PRESISI"
    assert response.json()["pesan"] == "Koordinat alamat belum presisi. Konfirmasi titik tepat di peta."
    assert response.json()["alamat_lengkap"] == "Alamat kasar tetapi berguna"
    assert response.json()["lat"] == pytest.approx(-6.9)
    assert response.json()["lng"] == pytest.approx(107.6)
    assert response.json()["granularitas"] == ("JALAN" if granularity == "RANGE_INTERPOLATED" else None)


@pytest.mark.parametrize("place_id", ["../rahasia", "a/b", "a b", "%2Fetc"])
def test_google_resolusi_menolak_place_id_tidak_aman_sebelum_http(place_id):
    calls = []
    adapter = GoogleGeoAdapter("secret", request_json=lambda *args: calls.append(args))
    with pytest.raises(ValueError, match="place_id tidak valid"):
        adapter.resolve_place(place_id)
    assert calls == []


def test_google_resolusi_respons_malformed_gagal_aman():
    adapter = GoogleGeoAdapter("secret", request_json=lambda *args: {"formattedAddress": "Tanpa koordinat"})
    with pytest.raises(ValueError, match="Respons penyedia alamat tidak valid"):
        adapter.resolve_place("abc")


def _provider_json_bytes(endpoint: str, size: int) -> bytes:
    payload = (
        {"suggestions": []}
        if endpoint == "autocomplete"
        else {
            "formattedAddress": "Alamat aman",
            "addressComponents": [],
            "location": {"latitude": -6.9, "longitude": 107.6},
            "granularity": "ROOFTOP",
            "placeId": "abc",
        }
    )
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    assert len(encoded) <= size
    return encoded + b" " * (size - len(encoded))


@pytest.mark.parametrize("endpoint", ["autocomplete", "resolusi"])
def test_google_response_tepat_batas_dibaca_dengan_limit_tambah_satu(monkeypatch, endpoint):
    limit = 512
    body = _provider_json_bytes(endpoint, limit)
    read_sizes = []

    class Response:
        headers = {"Content-Length": str(limit)}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, size):
            read_sizes.append(size)
            return body[:size]

    monkeypatch.setattr("urllib.request.urlopen", lambda request, timeout: Response())
    adapter = GoogleGeoAdapter("secret", max_response_bytes=limit)

    if endpoint == "autocomplete":
        assert adapter.autocomplete("cibiru", 5) == []
    else:
        assert adapter.resolve_place("abc").alamat == "Alamat aman"
    assert read_sizes == [limit + 1]


@pytest.mark.parametrize("endpoint", ["autocomplete", "resolusi"])
@pytest.mark.parametrize(
    ("content_length", "tambahan"),
    [
        ("513", 0),
        (None, 1),
        ("10", 1),
    ],
)
def test_google_response_oversize_ditolak_meski_content_length_hilang_atau_dipalsukan(
    monkeypatch, endpoint, content_length, tambahan
):
    limit = 512
    body = _provider_json_bytes(endpoint, limit) + b"x" * tambahan
    read_sizes = []

    class Response:
        headers = {} if content_length is None else {"Content-Length": content_length}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self, size):
            read_sizes.append(size)
            return body[:size]

    monkeypatch.setattr("urllib.request.urlopen", lambda request, timeout: Response())
    adapter = GoogleGeoAdapter("secret", max_response_bytes=limit)

    with pytest.raises(ValueError, match="Respons penyedia alamat terlalu besar") as error:
        adapter.autocomplete("cibiru", 5) if endpoint == "autocomplete" else adapter.resolve_place("abc")

    assert str(error.value) == "Respons penyedia alamat terlalu besar"
    assert body.decode("utf-8", errors="ignore") not in str(error.value)
    assert read_sizes == ([] if content_length == "513" else [limit + 1])


def test_api_saran_google_tidak_mengekspos_internal_provider(client, data_dasar, masuk, monkeypatch):
    from types import SimpleNamespace
    from app.adapters.geo.base import SuggestionResult
    from app.services import alamat_saran

    class Provider:
        def autocomplete(self, query, limit, bias=None, max_input=200, max_radius=50_000):
            assert query == "Cibiru Bandung"
            assert limit == 5
            return [
                SuggestionResult(
                    "abc_123",
                    "Cibiru",
                    "Cibiru, Bandung",
                    sumber="GOOGLE",
                    teks_sekunder="Jawa Barat",
                )
            ]

    settings = SimpleNamespace(
        geo_provider_enabled=True,
        google_maps_api_key="kunci-yang-tidak-boleh-bocor",
        geo_local_max_distance_km=25,
        alamat_saran_max_hasil=5,
        alamat_bias_radius_max_meter=20_000,
        alamat_provider_timeout_detik=3,
        jwt_secret="rahasia-token-lokal",
    )
    monkeypatch.setattr(alamat_saran, "get_settings", lambda: settings)
    monkeypatch.setattr(alamat_saran, "GoogleGeoAdapter", lambda key, timeout, **kwargs: Provider())

    response = client.post(
        "/api/alamat/saran",
        json={"query": "Cibiru Bandung"},
        headers=masuk("081200000012"),
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "saran": [
            {
                "place_id": "abc_123",
                "teks_utama": "Cibiru",
                "teks_lengkap": "Cibiru, Bandung",
                "teks_sekunder": "Jawa Barat",
                "sumber": "GOOGLE",
            }
        ],
        "status": "OK",
        "pesan": None,
    }
    serialized = response.text
    assert "kunci-yang-tidak-boleh-bocor" not in serialized
    assert "places.googleapis.com" not in serialized
    assert "X-Goog" not in serialized


def test_api_saran_provider_gagal_memakai_fallback_dengan_pesan_aman(
    client, data_dasar, masuk, wilayah_contoh, monkeypatch
):
    from types import SimpleNamespace
    from app.services import alamat_saran

    class Provider:
        def autocomplete(self, *args, **kwargs):
            raise RuntimeError("https://provider.invalid?key=SECRET rincian internal")

    settings = SimpleNamespace(
        geo_provider_enabled=True,
        google_maps_api_key="SECRET",
        geo_local_max_distance_km=25,
        alamat_saran_max_hasil=5,
        alamat_bias_radius_max_meter=20_000,
        alamat_provider_timeout_detik=3,
        jwt_secret="rahasia-token-lokal",
    )
    monkeypatch.setattr(alamat_saran, "get_settings", lambda: settings)
    monkeypatch.setattr(alamat_saran, "GoogleGeoAdapter", lambda key, timeout: Provider())

    response = client.post(
        "/api/alamat/saran",
        json={"query": "Cibiru"},
        headers=masuk("081200000012"),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "FALLBACK_LOKAL"
    assert response.json()["pesan"] == "Pencarian alamat presisi sedang tidak tersedia. Pilih wilayah lokal atau tentukan titik di peta."
    assert "SECRET" not in response.text
    assert "provider.invalid" not in response.text


def test_api_resolusi_google_mengembalikan_bentuk_kontrak(client, data_dasar, masuk, monkeypatch):
    from types import SimpleNamespace
    from app.adapters.geo.base import PlaceResolutionResult
    from app.services import alamat_saran

    class Provider:
        def resolve_place(self, place_id):
            assert place_id == "abc_123"
            return PlaceResolutionResult(
                alamat="Jl. Melati 7, Cibiru",
                jalan="Melati 7",
                kode_pos="40614",
                desa="Palasari",
                kecamatan="Cibiru",
                kabupaten="Kota Bandung",
                provinsi="Jawa Barat",
                lat=-6.91,
                lng=107.72,
                granularitas="ALAMAT",
                sumber="GOOGLE",
                koordinat_presisi=True,
            )

    settings = SimpleNamespace(
        geo_provider_enabled=True,
        google_maps_api_key="SECRET",
        geo_local_max_distance_km=25,
        alamat_provider_timeout_detik=3,
        jwt_secret="rahasia-token-lokal",
    )
    monkeypatch.setattr(alamat_saran, "get_settings", lambda: settings)
    monkeypatch.setattr(alamat_saran, "GoogleGeoAdapter", lambda key, timeout, **kwargs: Provider())

    response = client.post(
        "/api/alamat/resolusi",
        json={"place_id": "abc_123"},
        headers=masuk("081200000012"),
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
        "alamat_lengkap": "Jl. Melati 7, Cibiru",
        "jalan": "Melati 7",
        "kode_pos": "40614",
        "desa": "Palasari",
        "kecamatan": "Cibiru",
        "kabupaten_kota": "Kota Bandung",
        "provinsi": "Jawa Barat",
        "lat": -6.91,
        "lng": 107.72,
        "granularitas": "ALAMAT",
        "sumber": "GOOGLE",
        "status": "OK",
        "pesan": None,
    }


def test_api_resolusi_token_lokal_tidak_memalsukan_koordinat_presisi(
    client, data_dasar, masuk, wilayah_contoh, monkeypatch
):
    from types import SimpleNamespace
    from app.services import alamat_saran

    monkeypatch.setattr(
        alamat_saran,
        "get_settings",
        lambda: SimpleNamespace(
            geo_provider_enabled=False,
            google_maps_api_key="",
            geo_local_max_distance_km=25,
            alamat_saran_max_hasil=5,
            alamat_bias_radius_max_meter=20_000,
            jwt_secret="rahasia-token-lokal",
        ),
    )
    header = masuk("081200000012")
    saran = client.post("/api/alamat/saran", json={"query": "Cibiru"}, headers=header).json()["saran"][0]
    response = client.post("/api/alamat/resolusi", json={"place_id": saran["place_id"]}, headers=header)

    assert response.status_code == 200, response.text
    assert response.json()["sumber"] == "LOKAL"
    assert response.json()["status"] == "KOORDINAT_TIDAK_PRESISI"
    assert response.json()["alamat_lengkap"] == "Cibiru, Kota Bandung, Jawa Barat"
    assert "lat" not in response.json()
    assert "lng" not in response.json()
    assert response.json()["pesan"] == "Koordinat wilayah masih kasar. Tentukan titik tepat di peta."


def test_api_resolusi_provider_malformed_memberi_error_aman(client, data_dasar, masuk, monkeypatch):
    from types import SimpleNamespace
    from app.services import alamat_saran

    class Provider:
        def resolve_place(self, place_id):
            raise ValueError("payload mentah SECRET")

    settings = SimpleNamespace(
        geo_provider_enabled=True,
        google_maps_api_key="SECRET",
        geo_local_max_distance_km=25,
        alamat_provider_timeout_detik=3,
        jwt_secret="rahasia-token-lokal",
    )
    monkeypatch.setattr(alamat_saran, "get_settings", lambda: settings)
    monkeypatch.setattr(alamat_saran, "GoogleGeoAdapter", lambda key, timeout: Provider())
    response = client.post(
        "/api/alamat/resolusi",
        json={"place_id": "abc_123"},
        headers=masuk("081200000012"),
    )

    assert response.status_code == 200
    assert response.json() == {
        "alamat_lengkap": None,
        "jalan": None,
        "kode_pos": None,
        "desa": None,
        "kecamatan": None,
        "kabupaten_kota": None,
        "provinsi": None,
        "granularitas": None,
        "sumber": "GOOGLE",
        "status": "TIDAK_DITEMUKAN",
        "pesan": "Alamat tidak dapat diselesaikan. Cari ulang atau tentukan titik di peta.",
    }
    assert "SECRET" not in response.text


def test_rate_limit_per_pengguna_dan_retry_after_test_safe(client, data_dasar, masuk, monkeypatch):
    from app.routers import alamat

    monkeypatch.setattr(alamat, "_rate_limit_config", lambda: (2, 60, 100))
    wati = masuk("081200000012")
    dedi = masuk("081200000013")

    assert client.post("/api/alamat/saran", json={"query": "Cibiru"}, headers=wati).status_code == 200
    assert client.post("/api/alamat/saran", json={"query": "Cibiru"}, headers=wati).status_code == 200
    dibatasi = client.post("/api/alamat/saran", json={"query": "Cibiru"}, headers=wati)
    pengguna_lain = client.post("/api/alamat/saran", json={"query": "Cibiru"}, headers=dedi)

    assert dibatasi.status_code == 429
    assert int(dibatasi.headers["Retry-After"]) >= 1
    assert dibatasi.json() == {"detail": "Terlalu banyak permintaan alamat. Coba lagi sebentar."}
    assert pengguna_lain.status_code == 200
