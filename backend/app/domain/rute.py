"""Rute dua tahap: jemput dulu, baru antar (K14).

Sampai v3 seluruh petani dianggap berangkat dari satu titik kumpul, sehingga
rute muatan hanyalah `titik kumpul → semua tujuan`. Itu tidak menggambarkan apa
yang sebenarnya dikerjakan petugas: dia berkeliling MENJEMPUT panen di lokasi
masing-masing petani lebih dulu, baru mengantarkannya. Akibatnya dua hal salah
sekaligus — petugas tidak punya alamat penjemputan untuk dituju, dan `jarak_km`
(yang menjadi dasar harga) tidak menghitung leg penjemputan sama sekali.

Modul ini MENYUSUN ulang, bukan mengganti: `urutkan_tujuan_nearest_neighbor`
di `armada.py` dipakai apa adanya, dua kali. Berkas `armada.py` sengaja tidak
disentuh — ia dikunci beserta testnya.

Modul domain MURNI (aturan keras CLAUDE.md #2): tanpa DB, tanpa I/O, tanpa
`datetime.now()`.
"""

from dataclasses import dataclass

from app.domain.armada import TujuanInput, TujuanTerurut, urutkan_tujuan_nearest_neighbor


@dataclass(frozen=True)
class RuteDuaTahap:
    jemput: list[TujuanTerurut]
    antar: list[TujuanTerurut]

    @property
    def jarak_total_km(self) -> float:
        return sum(t.jarak_segmen_km for t in self.jemput) + sum(t.jarak_segmen_km for t in self.antar)


def urutkan_rute_dua_tahap(
    gudang: tuple[float, float],
    jemput: list[TujuanInput],
    antar: list[TujuanInput],
    faktor_jalan: float,
) -> RuteDuaTahap:
    """gudang → semua titik jemput (nearest-neighbor) → semua tujuan (nearest-neighbor).

    Tahap kedua berangkat dari titik jemput TERAKHIR, bukan kembali ke gudang —
    truk tidak pulang dulu sebelum mengantar. Kalau tidak ada penjemputan sama
    sekali (mis. data lama), tahap antar tetap berangkat dari gudang, sehingga
    hasilnya persis sama dengan perilaku sebelum K14.

    Berlaku: `jarak_total_km == sum(seluruh jarak_segmen_km)`, sama seperti
    invarian rute satu tahap.
    """
    urutan_jemput = urutkan_tujuan_nearest_neighbor(gudang, jemput, faktor_jalan)

    # Titik berangkat tahap antar = koordinat perhentian jemput terakhir.
    posisi = gudang
    if urutan_jemput:
        terakhir = urutan_jemput[-1].penerima_id
        cocok = next((t for t in jemput if t.penerima_id == terakhir), None)
        if cocok is not None:
            posisi = (cocok.lat, cocok.lng)

    urutan_antar = urutkan_tujuan_nearest_neighbor(posisi, antar, faktor_jalan)
    return RuteDuaTahap(jemput=urutan_jemput, antar=urutan_antar)
