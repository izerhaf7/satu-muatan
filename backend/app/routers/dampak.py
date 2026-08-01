"""Endpoint Dashboard Dampak (§9.10) + sumber 'Ringkasan bulan ini' Beranda (§9.2).
Ringkasan = empat kartu semboyan (spec v2 §7.1), urutan jangan diubah."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_pengguna_aktif
from app.database import get_db
from app.models import Komoditas, Konfigurasi, Lot, Partisipasi, SerahTerima
from app.models.enums import StatusPartisipasi, StatusSlot, StatusSumber
from app.schemas.dampak import DampakBulananOut, DampakRingkasanOut, KartuDampakOut
from app.services import mesin
from app.services.konfigurasi import baca_konfigurasi
from app.services.otorisasi import query_slot_untuk_peran

router = APIRouter(prefix="/dampak", tags=["dampak"])


def _kumpulkan_dampak(db: Session, pengguna):
    """Hitung dampak per slot SELESAI (ter-scope per peran seperti daftar slot),
    lalu akumulasikan total + per bulan + bahan empat kartu semboyan (v2 §7)."""
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
    semua_partisipasi_dampak: list[mesin.PartisipasiDampak] = []

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
        semua_partisipasi_dampak.extend(partisipasi_dampak)
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

    # Bahan kartu Transparansi: slot SELESAI terbaru yang punya serah terima —
    # durasi transit terpanjang vs ambang rutenya.
    durasi_maks: int | None = None
    ambang_terakhir: int | None = None
    kode_terakhir: str | None = None
    for slot in slot_selesai:  # sudah urut dibuat_pada desc (terbaru dulu)
        st_rows = (
            db.query(SerahTerima)
            .join(Lot, SerahTerima.lot_id == Lot.id)
            .join(Partisipasi, Lot.partisipasi_id == Partisipasi.id)
            .filter(Partisipasi.slot_id == slot.id)
            .all()
        )
        if st_rows:
            durasi_maks = max(st.durasi_transit_menit for st in st_rows)
            ambang_terakhir = st_rows[0].ambang_transit_menit
            kode_terakhir = slot.kode
            break

    # Bahan kartu Keamanan Pangan: rata-rata sisa umur simpan saat tiba
    # (tersimpan per serah terima sejak v2 §6).
    sisa_nilai = [
        st.sisa_umur_simpan_persen
        for st in db.query(SerahTerima).filter(SerahTerima.sisa_umur_simpan_persen.isnot(None)).all()
    ]
    sisa_rata = round(sum(sisa_nilai) / len(sisa_nilai)) if sisa_nilai else None

    return {
        "truk_km_total": truk_km_total,
        "emisi_total": emisi_total,
        "penghematan_total": penghematan_total,
        "susut_total": susut_total if susut_ada_data else None,
        "per_bulan": per_bulan,
        "semua_partisipasi": semua_partisipasi_dampak,
        "durasi_maks": durasi_maks,
        "ambang_terakhir": ambang_terakhir,
        "kode_terakhir": kode_terakhir,
        "sisa_rata": sisa_rata,
    }


@router.get("/ringkasan", response_model=DampakRingkasanOut)
def dampak_ringkasan(pengguna=Depends(get_pengguna_aktif), db: Session = Depends(get_db)):
    """Empat kartu semboyan (spec v2 §7.1) — satu angka per semboyan, masing-masing
    dengan rumus + status_sumber. Tanpa data = null -> '—'. Urutan JANGAN diubah."""
    agregat = _kumpulkan_dampak(db, pengguna)
    konf_emisi = db.get(Konfigurasi, "faktor_emisi_kg_co2_per_km")
    ada_data = bool(agregat["per_bulan"])

    partisipasi = agregat["semua_partisipasi"]
    persen = mesin.persen_penghematan_ongkos(partisipasi) if partisipasi else None
    sub_biaya: str | None = None
    if partisipasi and persen is not None:
        total_vol = sum(p.volume_kg for p in partisipasi)
        atap_rata = round(sum(p.volume_kg * p.harga_atap_per_kg for p in partisipasi) / total_vol)
        final_rata = round(sum(p.volume_kg * p.harga_final_per_kg for p in partisipasi) / total_vol)
        sub_biaya = f"Rp{atap_rata:,} → Rp{final_rata:,} per kg".replace(",", ".")

    truk_km = agregat["truk_km_total"]
    return DampakRingkasanOut(
        biaya_logistik=KartuDampakOut(
            nilai=round(persen, 1) if persen is not None else None,
            satuan="%",
            rumus="persen_penghematan = (Σ harga_atap×vol − Σ harga_final×vol) / Σ harga_atap×vol × 100",
            status_sumber=StatusSumber.TERVERIFIKASI,
            catatan_sumber="Dihitung dari harga atap terkunci vs harga final tiap peserta (jaminan atap terhormat).",
            sub_teks=sub_biaya,
        ),
        emisi=KartuDampakOut(
            nilai=round(agregat["emisi_total"], 1) if ada_data else None,
            satuan="kg CO₂e",
            rumus="emisi_dihemat_kg_co2 = truk_km_dihemat × faktor_emisi_kg_co2_per_km",
            status_sumber=konf_emisi.status_sumber if konf_emisi else StatusSumber.ASUMSI,
            catatan_sumber=konf_emisi.catatan_sumber if konf_emisi else None,
            sub_teks=f"{round(truk_km)} truk-km tidak jadi ditempuh" if ada_data else None,
        ),
        transparansi_perjalanan=KartuDampakOut(
            nilai=float(agregat["durasi_maks"]) if agregat["durasi_maks"] is not None else None,
            satuan="menit",
            rumus="ambang_transit_menit = ceil(jarak_km / kecepatan_rata_kmh × 60 × faktor_toleransi_transit)",
            status_sumber=StatusSumber.ASUMSI,
            catatan_sumber="Kecepatan rata-rata & faktor toleransi masih perkiraan tim.",
            sub_teks=(
                f"dari ambang {agregat['ambang_terakhir']} menit · {agregat['kode_terakhir']}"
                if agregat["durasi_maks"] is not None
                else None
            ),
        ),
        keamanan_pangan=KartuDampakOut(
            nilai=float(agregat["sisa_rata"]) if agregat["sisa_rata"] is not None else None,
            satuan="%",
            rumus="sisa = umur_simpan_jam − Σ q10^((suhu−suhu_acuan)/10) × menit/60 (model Q10, telemetri)",
            status_sumber=StatusSumber.ASUMSI,
            catatan_sumber="Parameter Q10 & umur simpan dari literatur umum postharvest.",
            sub_teks="Sisa umur simpan saat tiba" if agregat["sisa_rata"] is not None else None,
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
