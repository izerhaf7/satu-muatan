"""Generator telemetri dummy (spec v2 §5/C2) — WAJIB DETERMINISTIK.

Input sama -> output sama, selalu. Tidak pakai `random` tanpa seed; variasi
kecil dibangkitkan dari fungsi sinus terhadap `seed` (bukan RNG), jadi hasil
identik di mesin mana pun, kapan pun.
"""

import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.paparan import SampelTelemetri, hitung_paparan
from app.models import Komoditas, Penerima, Telemetri, TitikKumpul
from app.models.enums import SumberTelemetri
from app.models.slot import Slot
from app.models.bukti import Pengiriman
from app.services.konfigurasi import baca_konfigurasi

_GESER_WIB_JAM = 7  # kurva harian mengikuti jam lokal WIB (puncak ~15.00)


def bangkitkan_telemetri(
    pengiriman_id: UUID,
    waktu_mulai: datetime,
    durasi_menit: int,
    interval_menit: int,
    lat_asal: float,
    lng_asal: float,
    lat_tujuan: float,
    lng_tujuan: float,
    suhu_dasar_c: float,
    amplitudo_suhu_c: float,
    seed: int,
) -> list[Telemetri]:
    """Bangkitkan sampel telemetri SIMULASI (belum disimpan — caller yang add/commit).

    Suhu: kurva harian sinusoidal (spec §5.2):
        suhu = suhu_dasar + amplitudo × sin( 2π × (jam − 9) / 24 )
        → puncak suhu_dasar+amplitudo sekitar jam 15.00 WIB
        + variasi kecil deterministik dari seed (sinus, bukan random murni).

    Kelembapan: berkebalikan dengan suhu, kisaran 55–85%.
    Posisi: interpolasi linear asal → tujuan.
    """
    if durasi_menit <= 0 or interval_menit <= 0:
        return []

    langkah = max(1, math.ceil(durasi_menit / interval_menit))
    hasil: list[Telemetri] = []
    for i in range(langkah + 1):
        menit = min(i * interval_menit, durasi_menit)
        waktu = waktu_mulai + timedelta(minutes=menit)
        jam_wib = (waktu + timedelta(hours=_GESER_WIB_JAM)).hour + (waktu + timedelta(hours=_GESER_WIB_JAM)).minute / 60

        kurva = suhu_dasar_c + amplitudo_suhu_c * math.sin(2 * math.pi * (jam_wib - 9) / 24)
        variasi = 0.7 * math.sin(seed + i * 1.7)  # deterministik, ±0,7 °C
        suhu = round(kurva + variasi, 2)

        kelembapan = 70 - (suhu - suhu_dasar_c) * 2 + 1.5 * math.cos(seed + i * 2.3)
        kelembapan = round(min(85.0, max(55.0, kelembapan)), 2)

        frac = menit / durasi_menit
        lat = round(lat_asal + (lat_tujuan - lat_asal) * frac, 6)
        lng = round(lng_asal + (lng_tujuan - lng_asal) * frac, 6)

        hasil.append(
            Telemetri(
                pengiriman_id=pengiriman_id,
                waktu=waktu,
                suhu_c=suhu,  # type: ignore[arg-type]  # Numeric menerima float
                kelembapan_persen=kelembapan,  # type: ignore[arg-type]
                lat=lat,
                lng=lng,
                sumber=SumberTelemetri.SIMULASI,
            )
        )
    return hasil


def pastikan_telemetri(db: Session, pengiriman: Pengiriman, slot: Slot) -> list[Telemetri]:
    """Lazy-generate + perpanjangan deterministik.

    Belum ada baris -> bangkitkan dari berangkat → tiba (atau sekarang kalau
    masih jalan). Sudah ada tapi perjalanan masih berjalan dan interval berikut
    sudah lewat -> regenerasi PENUH dengan seed yang sama (kurva identik,
    titik bertambah — superset deterministik, bukan data baru). Seed stabil
    dari UUID pengiriman; interval antar-regenerasi dijaga agar polling 3
    detik tidak menulis ulang terus-menerus.
    """
    if pengiriman.waktu_berangkat is None:
        return []

    interval = baca_konfigurasi(db, "interval_telemetri_menit")
    suhu_dasar = baca_konfigurasi(db, "suhu_dasar_c")
    amplitudo = baca_konfigurasi(db, "amplitudo_suhu_c")

    akhir = pengiriman.waktu_tiba or datetime.now(timezone.utc)
    ada = (
        db.query(Telemetri)
        .filter_by(pengiriman_id=pengiriman.id)
        .order_by(Telemetri.waktu)
        .all()
    )
    if ada:
        if pengiriman.waktu_tiba is not None and ada[-1].waktu >= pengiriman.waktu_tiba:
            return ada  # perjalanan tuntas dan sudah tercakup penuh
        if pengiriman.waktu_tiba is None and (akhir - ada[-1].waktu).total_seconds() < interval * 60:
            return ada  # masih jalan, sampel terakhir masih dalam interval berjalan
        for r in ada:
            db.delete(r)
        db.flush()

    titik_kumpul = db.get(TitikKumpul, slot.titik_kumpul_id)
    tujuan_terakhir = max(slot.tujuan, key=lambda t: t.urutan) if slot.tujuan else None
    penerima = db.get(Penerima, tujuan_terakhir.penerima_id) if tujuan_terakhir else None

    durasi = max(interval, int((akhir - pengiriman.waktu_berangkat).total_seconds() // 60))

    # Seed deterministik per pengiriman (UUID -> int stabil).
    seed = pengiriman.id.int % 10_000
    baris = bangkitkan_telemetri(
        pengiriman_id=pengiriman.id,
        waktu_mulai=pengiriman.waktu_berangkat,
        durasi_menit=durasi,
        interval_menit=interval,
        lat_asal=titik_kumpul.lat if titik_kumpul else 0.0,
        lng_asal=titik_kumpul.lng if titik_kumpul else 0.0,
        lat_tujuan=penerima.lat if penerima else 0.0,
        lng_tujuan=penerima.lng if penerima else 0.0,
        suhu_dasar_c=float(suhu_dasar),
        amplitudo_suhu_c=float(amplitudo),
        seed=seed,
    )
    # Lazy materialization: GET pertama / perpanjangan menulis baris (demo MockVendor).
    db.add_all(baris)
    db.commit()
    return baris


def sampel_domain_dari_baris(baris: list[Telemetri]) -> list[SampelTelemetri]:
    """Ubah baris telemetri menjadi sampel domain paparan (durasi = selisih
    antar-sampel; sampel pertama 0 menit)."""
    sampel: list[SampelTelemetri] = []
    waktu_sebelumnya = None
    for r in baris:
        menit = 0 if waktu_sebelumnya is None else int((r.waktu - waktu_sebelumnya).total_seconds() // 60)
        sampel.append(
            SampelTelemetri(
                suhu_c=float(r.suhu_c),
                kelembapan_persen=float(r.kelembapan_persen),
                menit_sejak_sebelumnya=menit,
            )
        )
        waktu_sebelumnya = r.waktu
    return sampel


def sisa_umur_simpan_persen(
    db: Session, pengiriman: Pengiriman, slot: Slot, komoditas: Komoditas | None
) -> int | None:
    """Sisa umur simpan (%) untuk satu pengiriman menurut parameter Q10 komoditas
    yang diberikan. None kalau belum ada sampel telemetri / komoditas tak ada."""
    if komoditas is None:
        return None
    baris = pastikan_telemetri(db, pengiriman, slot)
    if not baris:
        return None
    hasil = hitung_paparan(
        sampel_domain_dari_baris(baris),
        float(komoditas.q10),
        float(komoditas.suhu_acuan_c),
        komoditas.umur_simpan_jam,
    )
    return hasil.sisa_umur_simpan_persen
