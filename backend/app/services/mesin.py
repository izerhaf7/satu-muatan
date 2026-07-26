"""Indirection ke `app.domain.*` dengan fallback `stub_domain` (spec §13 — "jangan menunggu").

Router memanggil fungsi-fungsi di modul INI, tidak pernah `app.domain.*` atau
`stub_domain` langsung. Selama implementasi asli di `app.domain.*` (worktree
`sm-domain`, agent domain-engine) masih `raise NotImplementedError`, panggilan di
sini otomatis jatuh ke `stub_domain` (algoritma sama persis, sudah diverifikasi
terhadap KEPUTUSAN.md K1). Begitu `fase1/domain` merge ke branch ini, hasil
`app.domain.*` dipakai otomatis — tidak ada baris kode yang perlu diubah.
"""

from typing import Any, Callable, TypeVar

from app.domain import armada as _armada
from app.domain import atribusi as _atribusi
from app.domain import dampak as _dampak
from app.domain import harga as _harga
from app.services import stub_domain as _stub

_T = TypeVar("_T")


def _dengan_fallback(fungsi_domain: Callable[..., _T], fungsi_stub: Callable[..., _T]) -> Callable[..., _T]:
    def _panggil(*args: Any, **kwargs: Any) -> _T:
        try:
            return fungsi_domain(*args, **kwargs)
        except NotImplementedError:
            return fungsi_stub(*args, **kwargs)

    return _panggil


jarak_haversine_km = _dengan_fallback(_armada.jarak_haversine_km, _stub.jarak_haversine_km)
urutkan_tujuan_nearest_neighbor = _dengan_fallback(
    _armada.urutkan_tujuan_nearest_neighbor, _stub.urutkan_tujuan_nearest_neighbor
)
jarak_rute_km = _dengan_fallback(_armada.jarak_rute_km, _stub.jarak_rute_km)
biaya_kendaraan = _dengan_fallback(_armada.biaya_kendaraan, _stub.biaya_kendaraan)
rencana_armada = _dengan_fallback(_armada.rencana_armada, _stub.rencana_armada)

harga_atap_per_kg = _dengan_fallback(_harga.harga_atap_per_kg, _stub.harga_atap_per_kg)
harga_berjalan_per_kg = _dengan_fallback(_harga.harga_berjalan_per_kg, _stub.harga_berjalan_per_kg)
cek_luapan_kapasitas = _dengan_fallback(_harga.cek_luapan_kapasitas, _stub.cek_luapan_kapasitas)
tetapkan_harga_final = _dengan_fallback(_harga.tetapkan_harga_final, _stub.tetapkan_harga_final)

ambang_transit_menit = _dengan_fallback(_atribusi.ambang_transit_menit, _stub.ambang_transit_menit)
tentukan_atribusi = _dengan_fallback(_atribusi.tentukan_atribusi, _stub.tentukan_atribusi)

hitung_dampak = _dengan_fallback(_dampak.hitung_dampak, _stub.hitung_dampak)

# Re-ekspor dataclass/exception domain supaya router hanya perlu `from app.services import mesin`.
Tier = _armada.Tier
RencanaArmada = _armada.RencanaArmada
TujuanInput = _armada.TujuanInput
TujuanTerurut = _armada.TujuanTerurut
VolumeKosong = _armada.VolumeKosong
VolumeTerlaluBesar = _armada.VolumeTerlaluBesar
PartisipasiHarga = _harga.PartisipasiHarga
HasilPenetapanHarga = _harga.HasilPenetapanHarga
HasilCekLuapan = _harga.HasilCekLuapan
PartisipasiDampak = _dampak.PartisipasiDampak
Dampak = _dampak.Dampak
