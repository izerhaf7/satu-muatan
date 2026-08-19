"""Test unit `app/domain/rute_polyline.py` — gerak sepanjang rute dari polyline.

Modul murni, jadi testnya murni juga: `jarak_haversine_km` diimpor dari
`armada.py` sebagai sumber jarak — tidak perlu DB atau I/O apa pun.

Keputusan kontrak yang diuji di sini:
  - `decode_polyline` mengangkat `ValueError` pada input rusak
    (kode karakter jelek, hasil kosong, kurang dari dua titik).
  - `posisi_pada_polyline` dengan polyline SATU titik mengembalikan titik itu;
    dengan polyline KOSONG mengangkat `ValueError` (tidak ada titik untuk
    dijadikan posisi).
"""

import pytest

from app.domain.armada import jarak_haversine_km
from app.domain.rute_polyline import decode_polyline, panjang_polyline_km, posisi_pada_polyline

# Contoh kanonik dari dokumentasi resmi Google (presisi 1e-5 / 5 digit).
RUTE_CONTOH = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
HASIL_CONTOH = [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)]


def _encode_polyline(titik: list[tuple[float, float]], presisi: int = 5) -> str:
    """Encoder referensi untuk round-trip — sengaja hanya ada di file test.

    Bukan bagian dari modul produksi; dipakai untuk memverifikasi bahwa
    decoder menghasilkan kebalikan yang eksak dari encoder standar Google.
    """

    def _potongan(nilai: int) -> str:
        nilai = ~(nilai << 1) if nilai < 0 else (nilai << 1)
        huruf: list[str] = []
        while nilai >= 0x20:
            huruf.append(chr((0x20 | (nilai & 0x1F)) + 63))
            nilai >>= 5
        huruf.append(chr(nilai + 63))
        return "".join(huruf)

    skala = 10**presisi
    hasil: list[str] = []
    lat_sebelum = 0
    lng_sebelum = 0
    for lat, lng in titik:
        lat_kuantum = round(lat * skala)
        lng_kuantum = round(lng * skala)
        hasil.append(_potongan(lat_kuantum - lat_sebelum))
        hasil.append(_potongan(lng_kuantum - lng_sebelum))
        lat_sebelum = lat_kuantum
        lng_sebelum = lng_kuantum
    return "".join(hasil)


def test_decode_contoh_kanonik_google():
    """Contoh kanonik dari dokumentasi Google — harus terurai dengan presisi 5."""
    hasil = decode_polyline(RUTE_CONTOH)
    assert len(hasil) == len(HASIL_CONTOH)
    for (lat, lng), (lat_e, lng_e) in zip(hasil, HASIL_CONTOH):
        assert lat == pytest.approx(lat_e, abs=1e-6)
        assert lng == pytest.approx(lng_e, abs=1e-6)


def test_decode_round_trip_dengan_encoder_referensi():
    """Decoder = kebalikan encoder standar Google (round-trip idempoten)."""
    # Polylines minimal dua titik — decoder sengaja menolak <2 titik.
    for koordinat in [
        [(-6.95, 107.6), (-6.92, 107.7), (-6.9, 107.75)],
        [(38.5, -120.2), (40.7, -120.95), (43.252, -126.453)],
    ]:
        assert decode_polyline(_encode_polyline(koordinat)) == koordinat


def test_decode_menolak_input_rusak():
    with pytest.raises(ValueError):
        decode_polyline("%%%")  # kode karakter di luar rentang
    with pytest.raises(ValueError):
        decode_polyline("")  # kosong → nol titik
    with pytest.raises(ValueError):
        decode_polyline("_p~iF~ps|U")  # hanya satu pasang koordinat → <2 titik
    with pytest.raises(ValueError):
        decode_polyline("_p~iF~ps")  # terpotong di tengah nilai lng


def test_panjang_dua_titik_sama_dengan_haversine():
    polyline = [(0.0, 0.0), (0.0, 1.0)]
    diharapkan = jarak_haversine_km(0.0, 0.0, 0.0, 1.0)
    assert panjang_polyline_km(polyline) == pytest.approx(diharapkan)


def test_panjang_tiga_titik_jumlah_segmen():
    """Total = Σ haversine antar titik berurutan, BUKAN jarak ujung-ke-ujung."""
    polyline = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0)]
    total = (
        jarak_haversine_km(0.0, 0.0, 0.0, 1.0)
        + jarak_haversine_km(0.0, 1.0, 1.0, 1.0)
    )
    assert panjang_polyline_km(polyline) == pytest.approx(total)


def test_posisi_setengah_panjang_segmen_lurus():
    """Separuh panjang segmen lurus di ekuator → tengah segmen itu."""
    polyline = [(0.0, 0.0), (0.0, 1.0)]
    total = panjang_polyline_km(polyline)
    lat, lng = posisi_pada_polyline(polyline, total / 2)
    assert lat == pytest.approx(0.0, abs=1e-6)
    assert lng == pytest.approx(0.5, abs=1e-6)


def test_posisi_klamp_ujung_bawah_dan_atas():
    polyline = [(0.0, 0.0), (0.0, 1.0)]
    total = panjang_polyline_km(polyline)
    assert posisi_pada_polyline(polyline, -5.0) == polyline[0]
    assert posisi_pada_polyline(polyline, 0.0) == polyline[0]
    assert posisi_pada_polyline(polyline, total + 10.0) == polyline[1]


def test_posisi_mendarat_di_segmen_yang_benar():
    """Belokan 90° bersegi tak sama: membuktikan berjalan PER SEGMEN.

    `jarak_tempuh_km` = persis panjang segmen pertama → posisi harus di titik
    belok (2, 0). Interpolasi linier global akan menaruh posisi di ~(1.3, 0.7)
    karena jaraknya ~2/3 dari total — kalau hasilnya (2, 0), berarti posisi
    dihitung dari jarak kumulatif per segmen, bukan proporsi global.
    """
    polyline = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0)]
    segmen_pertama = jarak_haversine_km(0.0, 0.0, 2.0, 0.0)
    segmen_kedua = jarak_haversine_km(2.0, 0.0, 2.0, 1.0)

    belok = posisi_pada_polyline(polyline, segmen_pertama)
    assert belok[0] == pytest.approx(2.0, abs=1e-6)
    assert belok[1] == pytest.approx(0.0, abs=1e-6)

    # Tengah segmen kedua: (2, 0.5) — interpolasi linear lokal.
    tengah = posisi_pada_polyline(polyline, segmen_pertama + segmen_kedua / 2)
    assert tengah[0] == pytest.approx(2.0, abs=1e-6)
    assert tengah[1] == pytest.approx(0.5, abs=1e-6)


def test_polyline_berisi_satu_titik_tidak_meledak():
    """Degenerat: satu titik → posisi = titik itu sendiri, panjang = 0.0."""
    satu = [(3.0, 4.0)]
    assert panjang_polyline_km(satu) == 0.0
    assert posisi_pada_polyline(satu, 10.0) == (3.0, 4.0)
    assert posisi_pada_polyline(satu, -1.0) == (3.0, 4.0)
    assert panjang_polyline_km([]) == 0.0


def test_posisi_polyline_kosong_mengangkat_valueerror():
    """Kosong tidak punya titik untuk dijadikan posisi — lebih jujur raise."""
    with pytest.raises(ValueError):
        posisi_pada_polyline([], 5.0)
