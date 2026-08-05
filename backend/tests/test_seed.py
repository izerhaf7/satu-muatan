from app.models import Pengiriman, Slot, Telemetri
from seed.seed import seed_induk, seed_konfigurasi, seed_riwayat, seed_tier


def test_seed_riwayat_menghubungkan_telemetri_ke_pengiriman(db):
    seed_tier(db)
    seed_konfigurasi(db)
    seed_induk(db)
    db.commit()

    assert seed_riwayat(db) == 8
    db.commit()

    pengiriman_ids = {row.id for row in db.query(Pengiriman).all()}
    telemetri = db.query(Telemetri).all()

    assert db.query(Slot).count() == 8
    assert len(pengiriman_ids) == 8
    assert telemetri
    assert all(row.pengiriman_id in pengiriman_ids for row in telemetri)
