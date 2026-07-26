/** Stub Muat (§9.5, peran Koperasi) — dibangun penuh di Fase 2 (layar-operasi). */

import KeadaanKosong from "@/komponen/KeadaanKosong";

export default function Muat() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6">
      <h1 className="text-2xl font-bold text-tanah">Muat</h1>
      <KeadaanKosong pesan="Layar muat belum tersedia. Menyusul di Fase 2." teksAksi="Kembali ke Beranda" ke="/" />
    </main>
  );
}
