"""Skema Dashboard Dampak (§7, §9.10).

Aturan kejujuran: setiap kartu membawa rumus + status_sumber koefisiennya.
Nilai tanpa data = null → UI menampilkan "—", BUKAN angka nol."""

from pydantic import BaseModel

from app.models.enums import StatusSumber


class KartuDampakOut(BaseModel):
    nilai: float | None = None  # null = tidak ada data → tampil "—"
    satuan: str
    rumus: str  # tampil di tooltip (§7)
    status_sumber: StatusSumber  # ASUMSI diberi penanda visual berbeda
    catatan_sumber: str | None = None


class DampakRingkasanOut(BaseModel):
    truk_km_dihemat: KartuDampakOut
    emisi_dihemat_kg_co2: KartuDampakOut
    penghematan_ongkos_rp: KartuDampakOut
    susut_dicegah_kg: KartuDampakOut


class DampakBulananOut(BaseModel):
    """Satu baris per bulan — juga sumber 'Ringkasan bulan ini' Beranda (§9.2, K6)."""

    bulan: str  # "YYYY-MM"
    jumlah_kiriman: int
    penghematan_rp: int
    truk_km_dihemat: float
    emisi_kg: float
    susut_kg: float | None = None
