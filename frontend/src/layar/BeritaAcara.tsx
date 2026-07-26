/** Stub Berita Acara (§9.8, halaman siap cetak) — dibangun penuh di Fase 2 (layar-bukti). */

import KeadaanKosong from "@/komponen/KeadaanKosong";

export default function BeritaAcara() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6">
      <h1 className="text-2xl font-bold text-tanah">Berita Acara</h1>
      <KeadaanKosong pesan="Berita acara belum tersedia. Menyusul di Fase 2." teksAksi="Kembali ke Beranda" ke="/" />
    </main>
  );
}
