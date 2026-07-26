"""MockVendorAdapter — WAJIB, dipakai untuk demo (spec §8.2).

Kontrak perilaku (dibekukan Fase 0, diimplementasi agent api-backend Fase 1):
- Kuotasi dihitung dengan RUMUS YANG SAMA PERSIS dengan mesin harga internal
  (tarif dari tabel `tier_kendaraan`, biaya = tarif_dasar + round(tarif_per_km × km)).
- DETERMINISTIK: input sama → output sama. Tidak boleh ada random.
- `status()` memajukan state berdasarkan waktu simulasi yang tersimpan di DB:
  `pengiriman.status_vendor` menyimpan state machine, progresi dihitung dari
  now − waktu_berangkat vs ambang transit, dan bisa dimajukan eksplisit lewat
  POST /api/pengiriman/{id}/majukan (KEPUTUSAN.md K5).
- Jeda buatan 400 ms per panggilan agar terasa seperti panggilan jaringan sungguhan.
"""

from app.adapters.base import Kontak, Kuotasi, Pesanan, StatusPengiriman, Titik

JEDA_BUATAN_DETIK = 0.4  # konstanta teknis simulasi jaringan, bukan koefisien bisnis


class MockVendorAdapter:
    nama = "MOCK"

    def kuotasi(self, titik: list[Titik], tier_kode: str) -> Kuotasi:
        """Kuotasi deterministik memakai tarif tier dari DB (lewat service pemanggil)."""
        raise NotImplementedError("Implementasi Fase 1 — agent api-backend")

    def pesan(self, kuotasi_id: str, kontak: Kontak) -> Pesanan:
        """vendor_ref deterministik diturunkan dari kuotasi_id."""
        raise NotImplementedError("Implementasi Fase 1 — agent api-backend")

    def status(self, vendor_ref: str) -> StatusPengiriman:
        """Majukan state simulasi sesuai konvensi K5."""
        raise NotImplementedError("Implementasi Fase 1 — agent api-backend")
