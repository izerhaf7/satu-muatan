"""Foto contoh untuk data demo & jalan pintas demo (K14).

Foto muat kini WAJIB (lihat `routers/lot.py`). Data riwayat yang di-seed dan
tombol "berangkatkan" mode demo tidak melewati kamera, jadi keduanya butuh
gambar pengganti — dan gambar itu harus JELAS-JELAS pengganti, bukan foto palsu
yang menyamar sebagai bukti sungguhan.

Yang dipakai: PNG 1×1 piksel abu-abu. Ukurannya sepele, tidak menyerupai foto
apa pun, dan di UI tampil sebagai kotak kosong yang langsung terbaca sebagai
"tidak ada foto sungguhan di sini".
"""

# PNG 1×1 abu-abu netral, base64 — sengaja bukan gambar yang menyerupai barang.
FOTO_PLACEHOLDER_DEMO = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)
