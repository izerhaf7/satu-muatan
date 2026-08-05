"""Route shadow snapshots remain informational and never change pricing."""

import json
from datetime import date, datetime, timezone
from decimal import Decimal

from app.models import Partisipasi, Pengiriman, Slot, SlotJemput, SlotTujuan
from app.models.enums import StatusPartisipasi


def _response():
    return {
        "routes": [
            {
                "duration": "125.7s",
                "distanceMeters": 12345,
                "polyline": {"encodedPolyline": "encoded-rute"},
            }
        ]
    }


def test_google_routes_adapter_posts_exact_order_and_parses_shared_route_contract():
    from app.adapters.geo.base import RouteDisplayResult
    from app.adapters.routes.google import GoogleRoutesAdapter

    panggilan = []

    def request_json(url, timeout, headers, method, body):
        panggilan.append((url, timeout, headers, method, body))
        return _response()

    hasil = GoogleRoutesAdapter("kunci-rahasia", request_json=request_json).route(
        origin=(-7.0, 107.0),
        stops=[(-6.9, 107.1), (-6.8, 107.2)],
        destination=(-6.0, 108.0),
    )

    assert isinstance(hasil, RouteDisplayResult)
    assert hasil.polyline == "encoded-rute"
    assert hasil.jarak_km == 12.345
    assert hasil.durasi_menit == 3
    assert hasil.versi == 1
    assert hasil.sumber == "GOOGLE_ROUTES"
    url, _, headers, method, body = panggilan[0]
    assert url == "https://routes.googleapis.com/directions/v2:computeRoutes"
    assert method == "POST"
    assert headers == {
        "X-Goog-Api-Key": "kunci-rahasia",
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline",
        "Content-Type": "application/json",
    }
    assert json.loads(body) == {
        "origin": {"location": {"latLng": {"latitude": -7.0, "longitude": 107.0}}},
        "destination": {"location": {"latLng": {"latitude": -6.0, "longitude": 108.0}}},
        "intermediates": [
            {"location": {"latLng": {"latitude": -6.9, "longitude": 107.1}}},
            {"location": {"latLng": {"latitude": -6.8, "longitude": 107.2}}},
        ],
        "travelMode": "DRIVE",
        "optimizeWaypointOrder": False,
    }


def test_google_routes_adapter_allows_25_stops_and_rejects_26_without_request():
    from app.adapters.routes.google import GoogleRoutesAdapter

    panggilan = []
    adapter = GoogleRoutesAdapter("kunci-rahasia", request_json=lambda *args: panggilan.append(args) or _response())

    adapter.route((0.0, 0.0), [(float(i), float(i)) for i in range(25)], (1.0, 1.0))
    assert len(panggilan) == 1

    try:
        adapter.route((0.0, 0.0), [(float(i), float(i)) for i in range(26)], (1.0, 1.0))
    except ValueError as exc:
        assert "25" in str(exc)
    else:
        raise AssertionError("26 stops must be rejected")
    assert len(panggilan) == 1


def test_google_routes_adapter_rejects_malformed_provider_response():
    from app.adapters.routes.google import GoogleRoutesAdapter

    for response in ({}, {"routes": []}, {"routes": [{"duration": "1s", "distanceMeters": 1, "polyline": {"encodedPolyline": ""}}]}):
        adapter = GoogleRoutesAdapter("kunci-rahasia", request_json=lambda *args, response=response: response)
        try:
            adapter.route((0.0, 0.0), [], (1.0, 1.0))
        except ValueError:
            pass
        else:
            raise AssertionError("Malformed response must be rejected")


def test_snapshot_persists_ordered_route_and_leaves_canonical_prices_unchanged(db, data_dasar):
    from app.services.rute_snapshot import simpan_snapshot_rute

    tk = data_dasar["titik_kumpul"]
    penerima = data_dasar["penerima"]
    slot = Slot(
        kode="SM-SNAPSHOT-01",
        titik_kumpul_id=tk.id,
        tanggal_kirim=date.today(),
        cutoff_at=date.today(),
        jarak_km=Decimal("99.00"),
        biaya_total=777_000,
        harga_final_per_kg=3333,
    )
    db.add(slot)
    db.flush()
    partisipasi_pertama = Partisipasi(
        slot_id=slot.id,
        petani_id=data_dasar["pengguna"]["asep"].id,
        komoditas_id=data_dasar["komoditas"]["kubis"].id,
        volume_kg=300,
        harga_atap_per_kg=3333,
        status=StatusPartisipasi.TERDAFTAR,
    )
    partisipasi_kedua = Partisipasi(
        slot_id=slot.id,
        petani_id=data_dasar["pengguna"]["wati"].id,
        komoditas_id=data_dasar["komoditas"]["kubis"].id,
        volume_kg=300,
        harga_atap_per_kg=3333,
        status=StatusPartisipasi.TERDAFTAR,
    )
    db.add_all([partisipasi_pertama, partisipasi_kedua])
    db.flush()
    db.add_all(
        [
            SlotJemput(slot_id=slot.id, partisipasi_id=partisipasi_kedua.id, urutan=2, lat=-7.2, lng=107.2, alamat="Jemput dua", jarak_segmen_km=Decimal("1")),
            SlotJemput(slot_id=slot.id, partisipasi_id=partisipasi_pertama.id, urutan=1, lat=-7.1, lng=107.1, alamat="Jemput satu", jarak_segmen_km=Decimal("1")),
            SlotTujuan(slot_id=slot.id, penerima_id=penerima["ujungberung"].id, urutan=2, jarak_segmen_km=Decimal("1")),
            SlotTujuan(slot_id=slot.id, penerima_id=penerima["cibiru"].id, urutan=1, jarak_segmen_km=Decimal("1")),
        ]
    )
    pengiriman = Pengiriman(slot_id=slot.id, vendor="MOCK")
    db.add(pengiriman)
    db.commit()

    panggilan = []

    class Adapter:
        def route(self, origin, stops, destination):
            from app.adapters.geo.base import RouteDisplayResult

            panggilan.append((origin, stops, destination))
            return RouteDisplayResult(jarak_km=12.345, durasi_menit=126, sumber="GOOGLE_ROUTES", polyline="encoded", versi=1)

    tetap = datetime(2026, 8, 4, 9, 30, tzinfo=timezone.utc)
    harga_partisipasi_sebelum = [(p.harga_atap_per_kg, p.harga_final_per_kg) for p in (partisipasi_pertama, partisipasi_kedua)]
    assert simpan_snapshot_rute(db, pengiriman, slot, adapter=Adapter(), sekarang=lambda: tetap) is True
    assert panggilan == [
        ((tk.lat, tk.lng), [(-7.1, 107.1), (-7.2, 107.2), (penerima["cibiru"].lat, penerima["cibiru"].lng)], (penerima["ujungberung"].lat, penerima["ujungberung"].lng))
    ]
    assert pengiriman.rute_polyline == "encoded"
    assert pengiriman.rute_versi == 1
    assert pengiriman.rute_jarak_provider_km == Decimal("12.345")
    assert pengiriman.rute_durasi_provider_menit == 126
    assert pengiriman.rute_sumber == "GOOGLE_ROUTES"
    assert pengiriman.rute_dihitung_pada == tetap
    assert slot.jarak_km == Decimal("99.00")
    assert slot.biaya_total == 777_000
    assert slot.harga_final_per_kg == 3333
    assert [(p.harga_atap_per_kg, p.harga_final_per_kg) for p in (partisipasi_pertama, partisipasi_kedua)] == harga_partisipasi_sebelum
    assert simpan_snapshot_rute(db, pengiriman, slot, adapter=Adapter()) is False
    assert len(panggilan) == 1
    db.expire_all()
    tersimpan = db.get(Pengiriman, pengiriman.id)
    assert tersimpan.rute_polyline == "encoded"
    assert tersimpan.rute_versi == 1
    assert tersimpan.rute_dihitung_pada == tetap


def test_snapshot_skips_same_waypoint_hash_and_falls_back_on_disabled_or_provider_error(db, data_dasar):
    from app.services.rute_snapshot import simpan_snapshot_rute

    tk = data_dasar["titik_kumpul"]
    slot = Slot(kode="SM-SNAPSHOT-02", titik_kumpul_id=tk.id, tanggal_kirim=date.today(), cutoff_at=date.today(), jarak_km=Decimal("1"))
    db.add(slot)
    db.flush()
    pengiriman = Pengiriman(slot_id=slot.id, vendor="MOCK")
    db.add(pengiriman)
    db.commit()

    class Meledak:
        def route(self, origin, stops, destination):
            raise OSError("provider down")

    assert simpan_snapshot_rute(db, pengiriman, slot, adapter=Meledak()) is False
    assert pengiriman.rute_polyline is None
    assert simpan_snapshot_rute(db, pengiriman, slot, enabled=False) is False


def test_snapshot_recomputes_changed_waypoints_and_keeps_invalid_response_nonfatal(db, data_dasar):
    from app.adapters.geo.base import RouteDisplayResult
    from app.services.rute_snapshot import simpan_snapshot_rute

    tk = data_dasar["titik_kumpul"]
    penerima = data_dasar["penerima"]["cibiru"]
    slot = Slot(kode="SM-SNAPSHOT-04", titik_kumpul_id=tk.id, tanggal_kirim=date.today(), cutoff_at=date.today(), jarak_km=Decimal("1"))
    db.add(slot)
    db.flush()
    db.add(SlotTujuan(slot_id=slot.id, penerima_id=penerima.id, urutan=1, jarak_segmen_km=Decimal("1")))
    pengiriman = Pengiriman(slot_id=slot.id, vendor="MOCK")
    db.add(pengiriman)
    db.commit()

    class Adapter:
        def __init__(self):
            self.panggilan = 0

        def route(self, origin, stops, destination):
            self.panggilan += 1
            return RouteDisplayResult(
                jarak_km=1.0, durasi_menit=1, sumber="GOOGLE_ROUTES", polyline=f"encoded-{self.panggilan}", versi=1
            )

    adapter = Adapter()
    assert simpan_snapshot_rute(db, pengiriman, slot, adapter=adapter, sekarang=lambda: datetime(2026, 8, 4)) is True
    assert pengiriman.rute_dihitung_pada == datetime(2026, 8, 4, tzinfo=timezone.utc)
    penerima.lng = 107.7199
    db.flush()
    assert simpan_snapshot_rute(db, pengiriman, slot, adapter=adapter, sekarang=lambda: datetime(2026, 8, 4, 1, tzinfo=timezone.utc)) is True
    assert adapter.panggilan == 2
    assert pengiriman.rute_versi == 2
    assert pengiriman.rute_polyline == "encoded-2"
    db.expire_all()
    tersimpan = db.get(Pengiriman, pengiriman.id)
    assert tersimpan.rute_versi == 2
    assert tersimpan.rute_polyline == "encoded-2"

    class Invalid:
        def route(self, origin, stops, destination):
            return RouteDisplayResult(jarak_km=1.0, durasi_menit=1, sumber="GOOGLE_ROUTES", polyline="", versi=1)

    pengiriman.rute_input_hash = None
    assert simpan_snapshot_rute(db, pengiriman, slot, adapter=Invalid()) is False


def test_pengiriman_output_keeps_legacy_null_route_fields(client, data_dasar, masuk, db):
    from app.models import Pengiriman, Slot

    tk = data_dasar["titik_kumpul"]
    slot = Slot(
        kode="SM-SNAPSHOT-03",
        titik_kumpul_id=tk.id,
        petugas_id=data_dasar["pengguna"]["titik_kumpul"].id,
        tanggal_kirim=date.today(),
        cutoff_at=date.today(),
        jarak_km=Decimal("1"),
    )
    db.add(slot)
    db.flush()
    pengiriman = Pengiriman(slot_id=slot.id, vendor="MOCK")
    db.add(pengiriman)
    db.commit()

    response = client.get(f"/api/slot/{slot.id}/pengiriman", headers=masuk("081200000001"))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["rute_polyline"] is None
    assert body["rute_versi"] is None
    assert body["eta_sumber"] is None
    assert body["eta_dihitung_pada"] is None
    assert "jemput" not in body


def test_snapshot_commit_failure_rolls_back_only_snapshot_changes(db, data_dasar, monkeypatch):
    from app.adapters.geo.base import RouteDisplayResult
    from app.services import rute_snapshot

    tk = data_dasar["titik_kumpul"]
    penerima = data_dasar["penerima"]["cibiru"]
    slot = Slot(kode="SM-SNAPSHOT-COMMIT", titik_kumpul_id=tk.id, tanggal_kirim=date.today(), cutoff_at=date.today(), jarak_km=Decimal("80"), harga_final_per_kg=1107)
    db.add(slot)
    db.flush()
    db.add(SlotTujuan(slot_id=slot.id, penerima_id=penerima.id, urutan=1, jarak_segmen_km=Decimal("80")))
    pengiriman = Pengiriman(slot_id=slot.id, vendor="MOCK", vendor_ref="canonical-order")
    db.add(pengiriman)
    db.commit()

    class Adapter:
        def route(self, origin, stops, destination):
            return RouteDisplayResult(jarak_km=80.0, durasi_menit=120, sumber="GOOGLE_ROUTES", polyline="encoded", versi=1)

    monkeypatch.setattr(rute_snapshot, "_commit_snapshot", lambda sesi: (_ for _ in ()).throw(RuntimeError("snapshot commit down")))
    assert rute_snapshot.simpan_snapshot_rute(db, pengiriman, slot, adapter=Adapter()) is False
    db.expire_all()
    tersimpan_slot = db.get(Slot, slot.id)
    tersimpan_pengiriman = db.get(Pengiriman, pengiriman.id)
    assert tersimpan_slot.harga_final_per_kg == 1107
    assert tersimpan_pengiriman.vendor_ref == "canonical-order"
    assert tersimpan_pengiriman.rute_polyline is None


def test_snapshot_same_hash_fresh_session_calls_provider_once(db, data_dasar):
    from app.adapters.geo.base import RouteDisplayResult
    from app.database import SessionLocal
    from app.services.rute_snapshot import simpan_snapshot_rute

    tk = data_dasar["titik_kumpul"]
    penerima = data_dasar["penerima"]["cibiru"]
    slot = Slot(kode="SM-SNAPSHOT-LOCK", titik_kumpul_id=tk.id, tanggal_kirim=date.today(), cutoff_at=date.today(), jarak_km=Decimal("1"))
    db.add(slot)
    db.flush()
    db.add(SlotTujuan(slot_id=slot.id, penerima_id=penerima.id, urutan=1, jarak_segmen_km=Decimal("1")))
    pengiriman = Pengiriman(slot_id=slot.id, vendor="MOCK")
    db.add(pengiriman)
    db.commit()

    class Adapter:
        calls = 0

        def route(self, origin, stops, destination):
            type(self).calls += 1
            return RouteDisplayResult(jarak_km=1.0, durasi_menit=1, sumber="GOOGLE_ROUTES", polyline="encoded", versi=1)

    assert simpan_snapshot_rute(db, pengiriman, slot, adapter=Adapter()) is True
    sesi_lain = SessionLocal()
    try:
        pengiriman_lain = sesi_lain.get(Pengiriman, pengiriman.id)
        slot_lain = sesi_lain.get(Slot, slot.id)
        assert pengiriman_lain is not None
        assert slot_lain is not None
        assert simpan_snapshot_rute(sesi_lain, pengiriman_lain, slot_lain, adapter=Adapter()) is False
    finally:
        sesi_lain.close()
    assert Adapter.calls == 1
