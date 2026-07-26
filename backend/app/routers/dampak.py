"""Endpoint Dashboard Dampak (§9.10) + sumber 'Ringkasan bulan ini' Beranda (§9.2)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_pengguna_aktif
from app.database import get_db
from app.models import Komoditas, Konfigurasi
from app.models.enums import StatusPartisipasi, StatusSlot, StatusSumber
from app.schemas.dampak import DampakBulananOut, DampakRingkasanOut, KartuDampakOut
from app.services import mesin
from app.services.konfigurasi import baca_konfigurasi
from app.services.otorisasi import query_slot_untuk_peran

router = APIRouter(prefix="/dampak", tags=["dampak"])


def _kumpulkan_dampak(db: Session, pengguna):
    """Hitung dampak per slot SELESAI (ter-scope per peran seperti daftar slot),
    lalu akumulasikan total + per bulan."""
    slot_selesai = query_slot_untuk_peran(db, pengguna, StatusSlot.SELESAI)
    faktor_emisi = baca_konfigurasi(db, "faktor_emisi_kg_co2_per_km")
    try:
        jam_dihemat = baca_konfigurasi(db, "jam_dihemat_per_kirim")
    except KeyError:
        jam_dihemat = None
    laju_susut_by_komoditas = {k.id: float(k.laju_susut_per_jam) for k in db.query(Komoditas).all()}

    truk_km_total = 0.0
    emisi_total = 0.0
    penghematan_total = 0
    susut_total = 0.0
    susut_ada_data = False
    per_bulan: dict[str, dict] = {}

    for slot in slot_selesai:
        partisipasi_aktif = [p for p in slot.partisipasi if p.status != StatusPartisipasi.BATAL and p.harga_final_per_kg is not None]
        if not partisipasi_aktif:
            continue
        partisipasi_dampak = [
            mesin.PartisipasiDampak(
                id=p.id,
                volume_kg=p.volume_kg,
                harga_atap_per_kg=p.harga_atap_per_kg,
                harga_final_per_kg=p.harga_final_per_kg,
                komoditas_id=p.komoditas_id,
            )
            for p in partisipasi_aktif
        ]
        jumlah_partisipan = len({p.petani_id for p in partisipasi_aktif})
        hasil = mesin.hitung_dampak(
            jumlah_partisipan, float(slot.jarak_km), partisipasi_dampak, faktor_emisi, laju_susut_by_komoditas, jam_dihemat
        )

        truk_km_total += hasil.truk_km_dihemat
        emisi_total += hasil.emisi_dihemat_kg_co2
        penghematan_total += hasil.penghematan_ongkos_rp
        if hasil.susut_dicegah_kg is not None:
            susut_total += hasil.susut_dicegah_kg
            susut_ada_data = True

        bulan_key = slot.tanggal_kirim.strftime("%Y-%m")
        entri = per_bulan.setdefault(
            bulan_key,
            {"jumlah_kiriman": 0, "penghematan_rp": 0, "truk_km_dihemat": 0.0, "emisi_kg": 0.0, "susut_kg": 0.0, "susut_ada": False},
        )
        entri["jumlah_kiriman"] += 1
        entri["penghematan_rp"] += hasil.penghematan_ongkos_rp
        entri["truk_km_dihemat"] += hasil.truk_km_dihemat
        entri["emisi_kg"] += hasil.emisi_dihemat_kg_co2
        if hasil.susut_dicegah_kg is not None:
            entri["susut_kg"] += hasil.susut_dicegah_kg
            entri["susut_ada"] = True

    return {
        "truk_km_total": truk_km_total,
        "emisi_total": emisi_total,
        "penghematan_total": penghematan_total,
        "susut_total": susut_total if susut_ada_data else None,
        "per_bulan": per_bulan,
    }


@router.get("/ringkasan", response_model=DampakRingkasanOut)
def dampak_ringkasan(pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    """4 kartu, masing-masing dengan rumus + status_sumber. Tanpa data = null -> '—'."""
    agregat = _kumpulkan_dampak(db, pengguna)
    konf_emisi = db.get(Konfigurasi, "faktor_emisi_kg_co2_per_km")
    konf_jam_dihemat = db.get(Konfigurasi, "jam_dihemat_per_kirim")
    ada_data = bool(agregat["per_bulan"])

    return DampakRingkasanOut(
        truk_km_dihemat=KartuDampakOut(
            nilai=agregat["truk_km_total"] if ada_data else None,
            satuan="km",
            rumus="truk_km_dihemat = (jumlah_partisipan − 1) × jarak_km, dibanding tiap petani mengirim sendiri-sendiri.",
            status_sumber=StatusSumber.TERVERIFIKASI,
            catatan_sumber="Dihitung dari jumlah peserta & jarak rute aktual tiap slot SELESAI.",
        ),
        emisi_dihemat_kg_co2=KartuDampakOut(
            nilai=agregat["emisi_total"] if ada_data else None,
            satuan="kg CO2e",
            rumus="emisi_dihemat_kg_co2 = truk_km_dihemat × faktor_emisi_kg_co2_per_km",
            status_sumber=konf_emisi.status_sumber if konf_emisi else StatusSumber.ASUMSI,
            catatan_sumber=konf_emisi.catatan_sumber if konf_emisi else None,
        ),
        penghematan_ongkos_rp=KartuDampakOut(
            nilai=agregat["penghematan_total"] if ada_data else None,
            satuan="Rp",
            rumus="penghematan_ongkos_rp = Σ volume_i × (harga_atap_i − harga_final_i)",
            status_sumber=StatusSumber.TERVERIFIKASI,
            catatan_sumber="Dihitung dari harga atap terkunci vs harga final tiap peserta (identik dengan Σ kembalian).",
        ),
        susut_dicegah_kg=KartuDampakOut(
            nilai=agregat["susut_total"],
            satuan="kg",
            rumus="susut_dicegah_kg = Σ volume_i × laju_susut_i × jam_dihemat_per_kirim (hanya jika data tersedia)",
            status_sumber=konf_jam_dihemat.status_sumber if konf_jam_dihemat else StatusSumber.ASUMSI,
            catatan_sumber=konf_jam_dihemat.catatan_sumber if konf_jam_dihemat else None,
        ),
    )


@router.get("/bulanan", response_model=list[DampakBulananOut])
def dampak_bulanan(pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    """Grafik batang per bulan (Recharts) — termasuk jumlah_kiriman (K6)."""
    agregat = _kumpulkan_dampak(db, pengguna)
    baris = [
        DampakBulananOut(
            bulan=bulan,
            jumlah_kiriman=entri["jumlah_kiriman"],
            penghematan_rp=entri["penghematan_rp"],
            truk_km_dihemat=entri["truk_km_dihemat"],
            emisi_kg=entri["emisi_kg"],
            susut_kg=entri["susut_kg"] if entri["susut_ada"] else None,
        )
        for bulan, entri in sorted(agregat["per_bulan"].items())
    ]
    return baris[-12:]
