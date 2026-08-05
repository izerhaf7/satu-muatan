"""Endpoint pendukung alamat (K14): autocomplete wilayah & reverse geocoding.

Keduanya dilayani BACKEND, bukan dipanggil langsung dari browser:
- daftar wilayah hidup di database kita sendiri, jadi autocomplete tetap jalan
  tanpa internet dan tanpa kuota pihak ketiga;
- reverse geocoding lewat proxy, sehingga kunci Google (kalau dipakai) tidak
  pernah ikut ter-bundle ke aplikasi.
"""

from collections import OrderedDict, deque
from math import ceil
from threading import Lock
from time import monotonic
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.auth import get_pengguna_aktif
from app.config import get_settings
from app.database import get_db
from app.models import Wilayah
from app.schemas.alamat import (
    AlamatResolusiOut,
    AlamatResolusiRequest,
    AlamatSaranItemOut,
    AlamatSaranListOut,
    AlamatSaranRequest,
    ErrorOut,
    GeokodeOut,
    GranularitasAlamat,
    StatusResolusiAlamat,
    SumberAlamat,
    WilayahOut,
)
from app.adapters.geo.local import LocalGeoAdapter
from app.services.geokode import geokode_balik
from app.services.alamat_saran import resolusi_alamat, saran_alamat

router = APIRouter(tags=["alamat"])

# Tingkat yang masuk akal diketik pengguna saat mengisi alamat.
_TINGKAT_DICARI = ("DESA", "KECAMATAN", "KABUPATEN")
_rate_lock = Lock()
_rate_events: OrderedDict[str, deque[float]] = OrderedDict()


def _rate_limit_config() -> tuple[int, int, int]:
    settings = get_settings()
    return (
        settings.alamat_rate_limit_per_jendela,
        settings.alamat_rate_limit_jendela_detik,
        settings.alamat_rate_limit_max_pengguna,
    )


def _cek_rate_limit(pengguna_id: str, response: Response) -> None:
    limit, window, max_users = _rate_limit_config()
    now = monotonic()
    with _rate_lock:
        events = _rate_events.setdefault(pengguna_id, deque())
        while events and events[0] <= now - window:
            events.popleft()
        if len(events) >= limit:
            retry_after = max(1, ceil(events[0] + window - now))
            response.headers["Retry-After"] = str(retry_after)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Terlalu banyak permintaan alamat. Coba lagi sebentar.",
                headers={"Retry-After": str(retry_after)},
            )
        events.append(now)
        _rate_events.move_to_end(pengguna_id)
        while len(_rate_events) > max_users:
            _rate_events.popitem(last=False)


@router.get("/wilayah/cari", response_model=list[WilayahOut])
def cari_wilayah(
    q: str = Query(min_length=2, description="Potongan nama desa/kecamatan/kabupaten"),
    batas: int = Query(default=10, ge=1, le=30),
    pengguna=Depends(get_pengguna_aktif),
    db: Session = Depends(get_db),
):
    """Autocomplete daerah dari tabel `wilayah` (data Kemendagri, di-seed lokal).

    Yang diawali kata kunci diutamakan daripada yang sekadar mengandungnya —
    mengetik "cika" harus memunculkan Cikajang lebih dulu, bukan nama panjang
    yang kebetulan memuat potongan itu di tengah."""
    baris = LocalGeoAdapter(db, get_settings().geo_local_max_distance_km).autocomplete(q, batas)
    return [
        WilayahOut(
            kode=w.place_id or "",
            nama=w.nama,
            tingkat=w.tingkat or "DESA",
            jalur=w.alamat or w.nama,
            kode_pos=w.kode_pos,
            lat=w.lat,
            lng=w.lng,
        )
        for w in baris
    ]


@router.get("/wilayah/anak", response_model=list[WilayahOut])
def anak_wilayah(
    tingkat: Literal["PROVINSI", "KABUPATEN", "KECAMATAN", "DESA"] = Query(),
    induk_kode: str | None = Query(default=None),
    pengguna=Depends(get_pengguna_aktif),
    db: Session = Depends(get_db),
):
    if tingkat == "PROVINSI" and induk_kode is not None:
        raise HTTPException(status_code=422, detail="PROVINSI tidak boleh memiliki induk_kode")
    if tingkat != "PROVINSI" and (induk_kode is None or not induk_kode.strip()):
        raise HTTPException(status_code=422, detail="induk_kode wajib diisi")

    query = db.query(
        Wilayah.kode,
        Wilayah.nama,
        Wilayah.tingkat,
        Wilayah.jalur,
        Wilayah.kode_pos,
        Wilayah.lat,
        Wilayah.lng,
        Wilayah.induk_kode,
    ).filter(Wilayah.tingkat == tingkat)
    if tingkat == "PROVINSI":
        query = query.filter(Wilayah.induk_kode.is_(None))
    else:
        query = query.filter(Wilayah.induk_kode == induk_kode)

    return [WilayahOut(**baris._asdict()) for baris in query.order_by(Wilayah.nama).all()]


@router.get("/geokode/balik", response_model=GeokodeOut)
def geokode_balik_endpoint(
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    pengguna=Depends(get_pengguna_aktif),
    db: Session = Depends(get_db),
):
    """Koordinat → alamat. Hasilnya di-cache per titik yang dibulatkan, jadi
    ketukan berulang di peta tidak pernah memanggil jaringan dua kali."""
    hasil = geokode_balik(db, lat, lng)
    return GeokodeOut(**hasil.__dict__)


@router.post(
    "/alamat/saran",
    response_model=AlamatSaranListOut,
    operation_id="saran_alamat_api_alamat_saran_post",
    summary="Saran Alamat",
    description=(
        "Cari paling banyak lima alamat untuk dipilih. `place_id` adalah token opaque yang hanya dikirim kembali "
        "ke `/api/alamat/resolusi`; browser tidak menerima URL, kunci, session token, atau objek mentah penyedia. "
        "Saat penyedia tidak tersedia, server dapat mengembalikan saran lokal atau respons tindakan aman untuk "
        "isian/peta manual."
    ),
    response_description="Saran alamat atau status fallback yang dapat ditindaklanjuti",
    responses={
        401: {"model": ErrorOut, "description": "Bearer token tidak ada atau tidak valid"},
        429: {
            "model": ErrorOut,
            "description": "Batas permintaan alamat tercapai; coba lagi setelah header Retry-After",
            "headers": {
                "Retry-After": {
                    "description": "Detik sampai klien boleh mencoba lagi.",
                    "schema": {"type": "integer", "minimum": 1},
                }
            },
        },
    },
)
def saran_alamat_endpoint(
    payload: AlamatSaranRequest,
    response: Response,
    pengguna=Depends(get_pengguna_aktif),
    db: Session = Depends(get_db),
):
    _cek_rate_limit(str(pengguna.id), response)
    bias = None
    if payload.bias is not None:
        settings = get_settings()
        bias = (
            payload.bias.lat,
            payload.bias.lng,
            min(payload.bias.radius_meter, settings.alamat_bias_radius_max_meter),
        )
    hasil, status_hasil, pesan = saran_alamat(db, payload.query, bias)
    return AlamatSaranListOut(
        saran=[
            AlamatSaranItemOut(
                place_id=item.place_id or "",
                teks_utama=item.nama,
                teks_lengkap=item.alamat or item.nama,
                teks_sekunder=item.teks_sekunder,
                sumber=SumberAlamat.GOOGLE if item.sumber == "GOOGLE" else SumberAlamat.LOKAL,
            )
            for item in hasil[:5]
        ],
        status=status_hasil,
        pesan=pesan,
    )


@router.post(
    "/alamat/resolusi",
    response_model=AlamatResolusiOut,
    response_model_exclude_none=False,
    operation_id="resolusi_alamat_api_alamat_resolusi_post",
    summary="Resolusi Alamat",
    description=(
        "Resolusi token `place_id` pilihan pengguna menjadi alamat terstruktur. Token lokal juga opaque dan "
        "diselesaikan server-side. `lat` dan `lng` selalu hadir bersama atau keduanya tidak ada; server menegakkan "
        "invarian lintas-field. Pada `KOORDINAT_TIDAK_PRESISI`, tampilkan pesan lalu minta pengguna memilih titik "
        "peta atau melengkapi alamat. `alamat_lengkap` wajib bernilai untuk `OK` dan "
        "`KOORDINAT_TIDAK_PRESISI`, dan null hanya untuk `TIDAK_DITEMUKAN`."
    ),
    response_description="Alamat terstruktur dan status ketelitian koordinat",
    responses={
        401: {"model": ErrorOut, "description": "Bearer token tidak ada atau tidak valid"},
        429: {
            "model": ErrorOut,
            "description": "Batas permintaan alamat tercapai; coba lagi setelah header Retry-After",
            "headers": {
                "Retry-After": {
                    "description": "Detik sampai klien boleh mencoba lagi.",
                    "schema": {"type": "integer", "minimum": 1},
                }
            },
        },
    },
)
def resolusi_alamat_endpoint(
    payload: AlamatResolusiRequest,
    response: Response,
    pengguna=Depends(get_pengguna_aktif),
    db: Session = Depends(get_db),
):
    _cek_rate_limit(str(pengguna.id), response)
    hasil, status_hasil, pesan = resolusi_alamat(db, payload.place_id)
    if hasil is None:
        return AlamatResolusiOut(
            alamat_lengkap=None,
            sumber=SumberAlamat.GOOGLE if not payload.place_id.startswith("lokal.") else SumberAlamat.LOKAL,
            status=StatusResolusiAlamat.TIDAK_DITEMUKAN,
            pesan=pesan,
        )
    return AlamatResolusiOut(
        alamat_lengkap=hasil.alamat,
        jalan=hasil.jalan,
        kode_pos=hasil.kode_pos,
        desa=hasil.desa,
        kecamatan=hasil.kecamatan,
        kabupaten_kota=hasil.kabupaten,
        provinsi=hasil.provinsi,
        lat=hasil.lat,
        lng=hasil.lng,
        granularitas=GranularitasAlamat(hasil.granularitas) if hasil.granularitas is not None else None,
        sumber=SumberAlamat(hasil.sumber),
        status=(
            StatusResolusiAlamat.OK
            if status_hasil == "OK"
            else StatusResolusiAlamat.KOORDINAT_TIDAK_PRESISI
            if status_hasil == "KOORDINAT_TIDAK_PRESISI"
            else StatusResolusiAlamat.TIDAK_DITEMUKAN
        ),
        pesan=pesan,
    )
