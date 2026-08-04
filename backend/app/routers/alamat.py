"""Endpoint pendukung alamat (K14): autocomplete wilayah & reverse geocoding.

Keduanya dilayani BACKEND, bukan dipanggil langsung dari browser:
- daftar wilayah hidup di database kita sendiri, jadi autocomplete tetap jalan
  tanpa internet dan tanpa kuota pihak ketiga;
- reverse geocoding lewat proxy, sehingga kunci Google (kalau dipakai) tidak
  pernah ikut ter-bundle ke aplikasi.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import get_pengguna_aktif
from app.database import get_db
from app.models import Wilayah
from app.schemas.alamat import GeokodeOut, WilayahOut
from app.services.geokode import geokode_balik

router = APIRouter(tags=["alamat"])

# Tingkat yang masuk akal diketik pengguna saat mengisi alamat.
_TINGKAT_DICARI = ("DESA", "KECAMATAN", "KABUPATEN")


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
    pola = q.strip().lower()
    baris = (
        db.query(Wilayah)
        .filter(Wilayah.tingkat.in_(_TINGKAT_DICARI))
        .filter(func.lower(Wilayah.nama).like(f"%{pola}%"))
        .order_by(
            # 0 = diawali kata kunci, 1 = sekadar mengandung.
            func.lower(Wilayah.nama).like(f"{pola}%").desc(),
            func.length(Wilayah.nama),
            Wilayah.nama,
        )
        .limit(batas)
        .all()
    )
    return [
        WilayahOut(
            kode=w.kode,
            nama=w.nama,
            tingkat=w.tingkat,
            jalur=w.jalur,
            kode_pos=w.kode_pos,
            lat=w.lat,
            lng=w.lng,
        )
        for w in baris
    ]


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
