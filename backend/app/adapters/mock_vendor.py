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

Adapter ini TIDAK menyentuh DB sendiri (murni terhadap parameter) — state
`status_vendor`/`waktu_berangkat`/`waktu_tiba` dibaca-tulis oleh service pemanggil
(`app.routers.lacak`), sejalan dengan cara `tier_kendaraan` di-inject sebagai
parameter `tiers` alih-alih di-query langsung oleh adapter.
"""

import hashlib
import time
import uuid

from app.adapters.base import Kontak, Kuotasi, Pesanan, StatusPengiriman, Titik
from app.domain.armada import Tier

JEDA_BUATAN_DETIK = 0.4  # konstanta teknis simulasi jaringan, bukan koefisien bisnis


def _jarak_titik_km(titik: list[Titik]) -> float:
    """Jarak rute akumulatif haversine MENTAH antar titik berurutan (titik[0] = gudang),
    belum dikoreksi faktor jalan — koreksi itu diterapkan oleh `kuotasi()` lewat
    `self._faktor_jalan`. `titik` dikirim pemanggil dalam urutan nearest-neighbor yang
    sama seperti dipakai saat `slot.jarak_km` dihitung, jadi hasil `kuotasi()` konsisten
    dengan `slot.jarak_km`."""
    from app.services.mesin import jarak_haversine_km

    total = 0.0
    for i in range(1, len(titik)):
        total += jarak_haversine_km(titik[i - 1].lat, titik[i - 1].lng, titik[i].lat, titik[i].lng)
    return total


class MockVendorAdapter:
    nama = "MOCK"

    def __init__(self, tiers: list[Tier], faktor_jalan: float = 1.0):
        """`tiers` di-inject oleh service pemanggil (dari `konfigurasi.baca_tiers_aktif`),
        adapter tidak pernah query DB sendiri. `faktor_jalan` dipakai untuk mengoreksi
        jarak lurus antar titik yang dikirim `kuotasi()` menjadi jarak jalan, identik
        dengan cara `slot.jarak_km` dihitung."""
        self._tiers = {t.kode: t for t in tiers}
        self._faktor_jalan = faktor_jalan

    def kuotasi(self, titik: list[Titik], tier_kode: str) -> Kuotasi:
        tier = self._tiers.get(tier_kode)
        if tier is None:
            raise ValueError(f"tier_kode tidak dikenal atau tidak aktif: {tier_kode}")
        time.sleep(JEDA_BUATAN_DETIK)
        jarak_km = _jarak_titik_km(titik) * self._faktor_jalan
        biaya_total = tier.tarif_dasar + round(tier.tarif_per_km * jarak_km)
        kuotasi_id = f"MOCKQ-{tier_kode}-{uuid.uuid5(uuid.NAMESPACE_URL, f'{tier_kode}:{jarak_km:.4f}').hex[:12]}"
        return Kuotasi(
            kuotasi_id=kuotasi_id,
            vendor=self.nama,
            tier_kode=tier_kode,
            biaya_total=biaya_total,
            rincian={
                "tier_kode": tier_kode,
                "jarak_km": round(jarak_km, 2),
                "tarif_dasar": tier.tarif_dasar,
                "tarif_per_km": tier.tarif_per_km,
                "biaya_total": biaya_total,
                "jumlah_titik": len(titik),
            },
        )

    def pesan(self, kuotasi_id: str, kontak: Kontak) -> Pesanan:
        """vendor_ref deterministik diturunkan dari kuotasi_id (tanpa random)."""
        time.sleep(JEDA_BUATAN_DETIK)
        vendor_ref = f"MOCKV-{hashlib.sha1(kuotasi_id.encode()).hexdigest()[:12].upper()}"
        return Pesanan(vendor_ref=vendor_ref, status="DIPESAN")

    def status(self, vendor_ref: str) -> StatusPengiriman:
        """Adapter murni tidak menyimpan state (tanpa DB) — state simulasi yang
        sesungguhnya (`pengiriman.status_vendor`, `waktu_berangkat`, `waktu_tiba`)
        dikelola oleh `app.routers.lacak` mengikuti konvensi K5. Method ini disediakan
        untuk memenuhi kontrak `VendorAdapter` dan mengembalikan status awal yang
        konsisten (DIPESAN, belum berangkat/tiba) untuk `vendor_ref` yang baru dipesan.
        """
        time.sleep(JEDA_BUATAN_DETIK)
        return StatusPengiriman(status="DIPESAN", waktu_berangkat=None, waktu_tiba=None)
