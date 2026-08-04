"""Test unit `app/domain/rute.py` (K14) — rute dua tahap: jemput lalu antar.

Modul murni, jadi testnya murni juga. `armada.py` sengaja TIDAK disentuh —
modul ini hanya menyusun ulang `urutkan_tujuan_nearest_neighbor` dua kali.
"""

from uuid import uuid4

from app.domain.armada import TujuanInput, jarak_haversine_km, urutkan_tujuan_nearest_neighbor
from app.domain.rute import urutkan_rute_dua_tahap

FAKTOR = 1.3
GUDANG = (-7.3661, 107.7961)  # Cikajang, Garut


def titik(lat: float, lng: float) -> TujuanInput:
    return TujuanInput(penerima_id=uuid4(), lat=lat, lng=lng)


def test_jarak_total_sama_dengan_jumlah_segmen():
    """Invarian yang sama dengan rute satu tahap — kalau ini pecah, harga bohong."""
    rute = urutkan_rute_dua_tahap(
        GUDANG,
        jemput=[titik(-7.36, 107.79), titik(-7.30, 107.78)],
        antar=[titik(-6.98, 107.62), titik(-6.93, 107.70)],
        faktor_jalan=FAKTOR,
    )
    segmen = [t.jarak_segmen_km for t in rute.jemput] + [t.jarak_segmen_km for t in rute.antar]
    assert rute.jarak_total_km == sum(segmen)


def test_urutan_menaik_dan_lengkap_di_kedua_tahap():
    jemput = [titik(-7.36, 107.79), titik(-7.30, 107.78), titik(-7.20, 107.75)]
    antar = [titik(-6.98, 107.62), titik(-6.93, 107.70)]
    rute = urutkan_rute_dua_tahap(GUDANG, jemput, antar, FAKTOR)

    assert [t.urutan for t in rute.jemput] == [1, 2, 3]
    assert [t.urutan for t in rute.antar] == [1, 2]
    assert {t.penerima_id for t in rute.jemput} == {t.penerima_id for t in jemput}
    assert {t.penerima_id for t in rute.antar} == {t.penerima_id for t in antar}


def test_tahap_antar_berangkat_dari_jemput_terakhir():
    """Truk TIDAK pulang ke gudang sebelum mengantar.

    Segmen pertama tahap antar harus diukur dari perhentian jemput terakhir,
    bukan dari gudang — kalau salah, jaraknya (dan harganya) meleset jauh."""
    jemput_titik = titik(-7.10, 107.70)
    antar_titik = titik(-6.93, 107.65)
    rute = urutkan_rute_dua_tahap(GUDANG, [jemput_titik], [antar_titik], FAKTOR)

    diharapkan = jarak_haversine_km(jemput_titik.lat, jemput_titik.lng, antar_titik.lat, antar_titik.lng) * FAKTOR
    assert rute.antar[0].jarak_segmen_km == diharapkan

    dari_gudang = jarak_haversine_km(GUDANG[0], GUDANG[1], antar_titik.lat, antar_titik.lng) * FAKTOR
    assert rute.antar[0].jarak_segmen_km != dari_gudang


def test_tanpa_penjemputan_sama_persis_dengan_rute_satu_tahap():
    """Kompatibilitas mundur: kiriman lama tanpa koordinat asal harus
    menghasilkan rute yang identik dengan sebelum K14."""
    antar = [titik(-6.98, 107.62), titik(-6.93, 107.70), titik(-6.90, 107.66)]
    dua_tahap = urutkan_rute_dua_tahap(GUDANG, [], antar, FAKTOR)
    satu_tahap = urutkan_tujuan_nearest_neighbor(GUDANG, antar, FAKTOR)

    assert dua_tahap.jemput == []
    assert dua_tahap.antar == satu_tahap


def test_jemput_diurutkan_nearest_neighbor_dari_gudang():
    dekat = titik(-7.36, 107.79)
    jauh = titik(-7.05, 107.72)
    rute = urutkan_rute_dua_tahap(GUDANG, [jauh, dekat], [], FAKTOR)
    assert rute.jemput[0].penerima_id == dekat.penerima_id
    assert rute.jemput[1].penerima_id == jauh.penerima_id


def test_rute_kosong_tidak_meledak():
    rute = urutkan_rute_dua_tahap(GUDANG, [], [], FAKTOR)
    assert rute.jemput == []
    assert rute.antar == []
    assert rute.jarak_total_km == 0
