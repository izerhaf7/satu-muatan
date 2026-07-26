"""DeliverreeAdapter — kerangka saja (spec §8.3).

Arsitekturnya adapter: yang jalan sekarang MockVendorAdapter dengan struktur
tarif publik asli; mengganti ke DeliverreeAdapter hanya soal kredensial API
produksi. Pemilihan lewat env `VENDOR_ADAPTER=MOCK|DELIVEREE`.
"""

from app.adapters.base import Kontak, Kuotasi, Pesanan, StatusPengiriman, Titik


class DeliverreeAdapter:
    """Adapter API Deliveree (https://www.deliveree.com) — belum aktif.

    Endpoint yang dibutuhkan saat kredensial tersedia:
    - POST quotations   → kuotasi()
    - POST bookings     → pesan()
    - GET  bookings/:id → status()
    """

    nama = "DELIVEREE"

    def kuotasi(self, titik: list[Titik], tier_kode: str) -> Kuotasi:
        """Minta kuotasi harga resmi untuk rute `titik` dengan tipe kendaraan `tier_kode`."""
        raise NotImplementedError("Butuh kredensial API produksi")

    def pesan(self, kuotasi_id: str, kontak: Kontak) -> Pesanan:
        """Buat pemesanan dari kuotasi yang sudah diterima."""
        raise NotImplementedError("Butuh kredensial API produksi")

    def status(self, vendor_ref: str) -> StatusPengiriman:
        """Tarik status pengiriman terkini dari vendor."""
        raise NotImplementedError("Butuh kredensial API produksi")
