"""Smoke test Fase 0: kontrak ter-import, app menyala, semua endpoint terdaftar.

Test angka mesin harga (tabel KEPUTUSAN.md K1) ditulis oleh agent domain-engine
di Fase 1 — test-first terhadap signature yang dibekukan di sini.
"""

from fastapi.testclient import TestClient

from app.main import app

RUTE_WAJIB = {
    ("POST", "/api/auth/masuk"),
    ("POST", "/api/auth/masuk-demo"),
    ("GET", "/api/auth/saya"),
    ("GET", "/api/komoditas"),
    ("GET", "/api/penerima"),
    ("GET", "/api/koperasi/saya"),
    ("GET", "/api/konfigurasi"),
    ("PATCH", "/api/konfigurasi/{kunci}"),
    ("GET", "/api/tier-kendaraan"),
    ("PATCH", "/api/tier-kendaraan/{tier_id}"),
    ("GET", "/api/permintaan"),
    ("POST", "/api/permintaan"),
    ("GET", "/api/slot"),
    ("POST", "/api/slot"),
    ("POST", "/api/slot/pratinjau"),
    ("GET", "/api/slot/{slot_id}"),
    ("POST", "/api/slot/{slot_id}/gabung"),
    ("POST", "/api/slot/{slot_id}/gabung/pratinjau"),
    ("POST", "/api/slot/{slot_id}/tutup"),
    ("POST", "/api/slot/{slot_id}/batal"),
    ("GET", "/api/slot/{slot_id}/lot"),
    ("PATCH", "/api/lot/{lot_id}/muat"),
    ("POST", "/api/slot/{slot_id}/selesai-muat"),
    ("GET", "/api/lot/masuk"),
    ("GET", "/api/lot/qr/{kode_qr}"),
    ("POST", "/api/lot/{lot_id}/serah-terima"),
    ("GET", "/api/slot/{slot_id}/pengiriman"),
    ("POST", "/api/pengiriman/{pengiriman_id}/majukan"),
    ("GET", "/api/slot/{slot_id}/berita-acara"),
    ("GET", "/api/dampak/ringkasan"),
    ("GET", "/api/dampak/bulanan"),
    ("GET", "/api/partisipasi/saya"),
    ("POST", "/api/demo/reset"),
    ("GET", "/healthz"),
}


def _rute_app() -> set[tuple[str, str]]:
    # Dibaca dari skema OpenAPI — artefak yang benar-benar dibekukan di kontrak/.
    # (FastAPI >=0.140 menyimpan router ter-include secara lazy di app.routes.)
    hasil = set()
    for path, methods in app.openapi()["paths"].items():
        for method in methods:
            hasil.add((method.upper(), path))
    return hasil


def test_semua_rute_kontrak_terdaftar():
    hilang = RUTE_WAJIB - _rute_app()
    assert not hilang, f"Rute kontrak hilang: {sorted(hilang)}"


def test_healthz():
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_domain_signatures_terimpor():
    from app.domain import armada, atribusi, dampak, harga

    assert callable(armada.rencana_armada)
    assert callable(harga.tetapkan_harga_final)
    assert callable(harga.cek_luapan_kapasitas)
    assert callable(atribusi.tentukan_atribusi)
    assert callable(dampak.hitung_dampak)


def test_openapi_terbentuk():
    skema = app.openapi()
    assert skema["info"]["title"] == "Satu Muatan API"
    assert "/api/slot/{slot_id}/gabung" in skema["paths"]
    # 409 LUAPAN_KAPASITAS terdokumentasi di kontrak (§5.5, K6)
    assert "409" in skema["paths"]["/api/slot/{slot_id}/gabung"]["post"]["responses"]
