"""Test domain dampak.py — kalkulator dampak keberlanjutan.

Acuan: spec §7, KEPUTUSAN.md K6. Penghematan wajib dihitung per peserta
(H_i = min(H_kasar, atap_i)), TIDAK PERNAH negatif. susut_dicegah_kg wajib
None (bukan 0.0) kalau jam_dihemat tidak tersedia.
"""

from uuid import uuid4

from app.domain.dampak import PartisipasiDampak, hitung_dampak

JARAK = 80.0


def test_hitung_dampak_t11_penghematan_sama_dengan_sigma_kembalian():
    # Pembanding: KEPUTUSAN.md K6/K1 T11 — A(800kg, atap 415, final 415, ter-cap
    # jaminan atap) + B(10kg, atap 27.100, final 671). Penghematan per peserta
    # HARUS pakai H_i milik peserta itu (bukan H_kasar global 671), jika tidak
    # A yang ter-cap akan menghasilkan penghematan negatif (K6, dilarang keras).
    komoditas_x = uuid4()
    id_a, id_b = uuid4(), uuid4()
    partisipasi = [
        PartisipasiDampak(id=id_a, volume_kg=800, harga_atap_per_kg=415, harga_final_per_kg=415, komoditas_id=komoditas_x),
        PartisipasiDampak(id=id_b, volume_kg=10, harga_atap_per_kg=27100, harga_final_per_kg=671, komoditas_id=komoditas_x),
    ]

    hasil = hitung_dampak(
        jumlah_partisipan=2,
        jarak_km=JARAK,
        partisipasi=partisipasi,
        faktor_emisi=0.25,
        laju_susut_per_jam={komoditas_x: 0.0025},
        jam_dihemat=None,
    )

    # Pembanding: Σ kembalian_i dari mesin harga (test_harga_domain T11) = 0 + 264.290.
    assert hasil.penghematan_ongkos_rp == 264290
    assert hasil.penghematan_ongkos_rp >= 0  # invarian K6: tidak pernah negatif


def test_hitung_dampak_truk_km_dan_emisi():
    # Pembanding: truk_km_dihemat = (n−1) × jarak — setiap petani mengirim
    # sendiri-sendiri jadi pembandingnya. emisi = truk_km × faktor_emisi.
    komoditas_x = uuid4()
    partisipasi = [
        PartisipasiDampak(id=uuid4(), volume_kg=300, harga_atap_per_kg=1107, harga_final_per_kg=1107, komoditas_id=komoditas_x),
    ]

    hasil = hitung_dampak(
        jumlah_partisipan=4,
        jarak_km=JARAK,
        partisipasi=partisipasi,
        faktor_emisi=0.25,
        laju_susut_per_jam={komoditas_x: 0.0025},
        jam_dihemat=None,
    )

    assert hasil.truk_km_dihemat == (4 - 1) * JARAK  # 240.0
    assert hasil.emisi_dihemat_kg_co2 == (4 - 1) * JARAK * 0.25  # 60.0


def test_hitung_dampak_susut_none_saat_jam_dihemat_tidak_tersedia():
    # Pembanding: tanpa data jam_dihemat, UI harus tampil "—" bukan 0 — jadi
    # nilainya harus None, bukan 0.0 (K6).
    komoditas_x = uuid4()
    partisipasi = [
        PartisipasiDampak(id=uuid4(), volume_kg=300, harga_atap_per_kg=1107, harga_final_per_kg=1107, komoditas_id=komoditas_x),
    ]

    hasil = hitung_dampak(
        jumlah_partisipan=2,
        jarak_km=JARAK,
        partisipasi=partisipasi,
        faktor_emisi=0.25,
        laju_susut_per_jam={komoditas_x: 0.0025},
        jam_dihemat=None,
    )

    assert hasil.susut_dicegah_kg is None


def test_hitung_dampak_susut_none_saat_jam_dihemat_nol():
    # Pembanding: jam_dihemat == 0 juga tidak dihitung (bukan hanya None) — spec
    # "HANYA dihitung kalau jam_dihemat tersedia DAN > 0".
    komoditas_x = uuid4()
    partisipasi = [
        PartisipasiDampak(id=uuid4(), volume_kg=300, harga_atap_per_kg=1107, harga_final_per_kg=1107, komoditas_id=komoditas_x),
    ]

    hasil = hitung_dampak(
        jumlah_partisipan=2,
        jarak_km=JARAK,
        partisipasi=partisipasi,
        faktor_emisi=0.25,
        laju_susut_per_jam={komoditas_x: 0.0025},
        jam_dihemat=0.0,
    )

    assert hasil.susut_dicegah_kg is None


def test_hitung_dampak_susut_dihitung_saat_jam_dihemat_tersedia():
    # Pembanding: susut_dicegah_kg = Σ volume_i × laju_susut_i × jam_dihemat,
    # di-key per komoditas_id (K6) — dua komoditas berbeda punya laju berbeda.
    komoditas_kubis = uuid4()
    komoditas_tomat = uuid4()
    id_a, id_b = uuid4(), uuid4()
    partisipasi = [
        PartisipasiDampak(id=id_a, volume_kg=300, harga_atap_per_kg=1107, harga_final_per_kg=1107, komoditas_id=komoditas_kubis),
        PartisipasiDampak(id=id_b, volume_kg=200, harga_atap_per_kg=1107, harga_final_per_kg=1107, komoditas_id=komoditas_tomat),
    ]
    laju = {komoditas_kubis: 0.0025, komoditas_tomat: 0.0052}
    jam_dihemat = 2.0

    hasil = hitung_dampak(
        jumlah_partisipan=2,
        jarak_km=JARAK,
        partisipasi=partisipasi,
        faktor_emisi=0.25,
        laju_susut_per_jam=laju,
        jam_dihemat=jam_dihemat,
    )

    acuan = 300 * 0.0025 * jam_dihemat + 200 * 0.0052 * jam_dihemat
    assert hasil.susut_dicegah_kg is not None
    assert hasil.susut_dicegah_kg == acuan
