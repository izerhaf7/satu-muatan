from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import buat_token, get_pengguna_aktif, hash_pin, verifikasi_pin
from app.config import get_settings
from app.database import get_db
from app.models import PeranPengguna, Pengguna, TitikKumpul
from app.schemas.auth import AkunDemo, DaftarRequest, MasukDemoRequest, MasukRequest, PenggunaOut, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Akun demo kanonik (v2 §8) — identitas tetap, bukan koefisien bisnis.
_NO_HP_AKUN_DEMO: dict[AkunDemo, str] = {
    AkunDemo.PETUGAS: "081200000011",  # Asep — petugas Titik Kumpul Pak Asep
    AkunDemo.PETANI_WATI: "081200000012",
    AkunDemo.PETANI_DEDI: "081200000013",
    AkunDemo.PETANI_IJAH: "081200000014",
    AkunDemo.PENERIMA_CIBIRU: "081200000021",
}


@router.post("/masuk", response_model=TokenResponse)
def masuk(body: MasukRequest, db: Session = Depends(get_db)):
    """Login nomor HP + PIN 6 digit (§9.1)."""
    pengguna = db.query(Pengguna).filter_by(no_hp=body.no_hp).one_or_none()
    if pengguna is None or not pengguna.aktif or not verifikasi_pin(body.pin, pengguna.pin_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Nomor HP atau PIN salah")
    token = buat_token(pengguna.id, pengguna.peran.value)
    return TokenResponse(token=token, pengguna=PenggunaOut.model_validate(pengguna))


@router.post("/daftar", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def daftar(body: DaftarRequest, db: Session = Depends(get_db)):
    """Daftar sendiri — Petani atau Penerima (§9.1 tambahan). PETUGAS sengaja
    tidak bisa daftar lewat sini (lihat `PeranDaftar`, hanya 2 nilai).

    Tanpa verifikasi OTP (keputusan produk) — nomor HP tidak dibuktikan
    kepemilikannya, cukup untuk demo. Auto-login setelah daftar, sama seperti
    `masuk()`."""
    if db.query(Pengguna).filter_by(no_hp=body.no_hp).one_or_none() is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Nomor HP ini sudah terdaftar. Coba masuk, atau pakai nomor lain."
        )

    titik_kumpul_id = None
    if body.peran == "PETANI":
        tk = (
            db.query(TitikKumpul)
            .filter(TitikKumpul.kode.isnot(None))
            .order_by(TitikKumpul.dibuat_pada)
            .first()
        )
        if tk is None:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Belum ada titik kumpul aktif, jalankan seed dulu.")
        titik_kumpul_id = tk.id

    pengguna = Pengguna(
        nama=body.nama,
        no_hp=body.no_hp,
        pin_hash=hash_pin(body.pin),
        peran=PeranPengguna(body.peran),
        titik_kumpul_id=titik_kumpul_id,
        aktif=True,
    )
    db.add(pengguna)
    db.commit()
    db.refresh(pengguna)

    token = buat_token(pengguna.id, pengguna.peran.value)
    return TokenResponse(token=token, pengguna=PenggunaOut.model_validate(pengguna))


@router.post("/masuk-demo", response_model=TokenResponse)
def masuk_demo(body: MasukDemoRequest, db: Session = Depends(get_db)):
    """Masuk cepat (demo) — hanya aktif saat DEMO_MODE (§9.1, K6: 6 akun)."""
    if not get_settings().demo_mode:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Mode demo tidak aktif")
    no_hp = _NO_HP_AKUN_DEMO[body.akun]
    pengguna = db.query(Pengguna).filter_by(no_hp=no_hp).one_or_none()
    if pengguna is None or not pengguna.aktif:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Akun demo belum tersedia — jalankan seed")
    token = buat_token(pengguna.id, pengguna.peran.value)
    return TokenResponse(token=token, pengguna=PenggunaOut.model_validate(pengguna))


@router.get("/saya", response_model=PenggunaOut)
def saya(pengguna=Depends(get_pengguna_aktif)):
    """Profil pengguna yang sedang login."""
    return PenggunaOut.model_validate(pengguna)
