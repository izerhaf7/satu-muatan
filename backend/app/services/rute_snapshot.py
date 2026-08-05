"""Best-effort, informational Google route snapshots after canonical pricing."""

import hashlib
import json
import math
from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.geo.base import RouteDisplayResult
from app.adapters.routes.google import GoogleRoutesAdapter
from app.config import get_settings
from app.models import Pengiriman, Penerima, Slot, TitikKumpul


def _waypoints(db: Session, slot: Slot) -> list[tuple[float, float]]:
    titik_kumpul = db.get(TitikKumpul, slot.titik_kumpul_id)
    if titik_kumpul is None:
        return []
    titik = [(titik_kumpul.lat, titik_kumpul.lng)]
    titik.extend((j.lat, j.lng) for j in sorted(slot.jemput, key=lambda j: j.urutan))
    for tujuan in sorted(slot.tujuan, key=lambda t: t.urutan):
        penerima = db.get(Penerima, tujuan.penerima_id)
        if penerima is not None:
            titik.append((penerima.lat, penerima.lng))
    return titik


def _input_hash(waypoints: list[tuple[float, float]]) -> str:
    encoded = json.dumps(waypoints, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _sekarang_utc() -> datetime:
    return datetime.now(timezone.utc)


def _waktu_utc(waktu: datetime) -> datetime:
    return waktu.replace(tzinfo=timezone.utc) if waktu.tzinfo is None else waktu.astimezone(timezone.utc)


def _pastikan_hasil(hasil: RouteDisplayResult) -> RouteDisplayResult:
    if (
        not isinstance(hasil.polyline, str)
        or not hasil.polyline
        or not math.isfinite(hasil.jarak_km)
        or hasil.jarak_km < 0
        or not math.isfinite(hasil.durasi_menit)
        or hasil.durasi_menit < 0
    ):
        raise ValueError("Snapshot rute provider tidak valid")
    return hasil


def _commit_snapshot(db: Session) -> None:
    db.commit()


def simpan_snapshot_rute(
    db: Session,
    pengiriman: Pengiriman,
    slot: Slot,
    *,
    adapter=None,
    enabled: bool | None = None,
    sekarang: Callable[[], datetime] = _sekarang_utc,
) -> bool:
    """Commit one informational snapshot transaction after canonical state commits.

    This function owns only its snapshot transaction. It locks `pengiriman` before
    comparing the route hash, calling provider, updating fields, and committing.
    Call only after caller has committed canonical pricing, lots, and vendor order.
    """
    settings = get_settings()
    aktif = settings.geo_provider_enabled if enabled is None else enabled
    if not aktif or (not settings.google_maps_api_key and adapter is None):
        return False

    try:
        terkunci = db.execute(select(Pengiriman).where(Pengiriman.id == pengiriman.id).with_for_update()).scalar_one()
        slot_terkunci = db.get(Slot, terkunci.slot_id)
        if slot_terkunci is None:
            db.rollback()
            return False
        titik = _waypoints(db, slot_terkunci)
        if len(titik) < 2:
            db.rollback()
            return False
        input_hash = _input_hash(titik)
        if terkunci.rute_input_hash == input_hash:
            db.rollback()
            return False
        hasil = _pastikan_hasil((adapter or GoogleRoutesAdapter(settings.google_maps_api_key)).route(titik[0], titik[1:-1], titik[-1]))
        terkunci.rute_polyline = hasil.polyline
        terkunci.rute_versi = (terkunci.rute_versi or 0) + 1
        terkunci.rute_input_hash = input_hash
        terkunci.rute_jarak_provider_km = Decimal(str(hasil.jarak_km))
        terkunci.rute_durasi_provider_menit = int(hasil.durasi_menit)
        terkunci.rute_dihitung_pada = _waktu_utc(sekarang())
        terkunci.rute_sumber = hasil.sumber
        _commit_snapshot(db)
    except Exception:
        db.rollback()
        return False
    db.refresh(pengiriman)
    return True
