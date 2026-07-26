/** Stub Riwayat (§2.5, layar utama Petani) — dibangun penuh di Fase 2. */

import KeadaanKosong from "@/komponen/KeadaanKosong";

export default function Riwayat() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6">
      <h1 className="text-2xl font-bold text-tanah">Riwayat</h1>
      <KeadaanKosong pesan="Riwayat pengiriman belum tersedia. Menyusul di Fase 2." teksAksi="Kembali ke Beranda" ke="/" />
    </main>
  );
}
