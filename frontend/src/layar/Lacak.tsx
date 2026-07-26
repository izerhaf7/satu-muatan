/** Stub Lacak (§9.6) — dibangun penuh di Fase 2 (layar-operasi). */

import KeadaanKosong from "@/komponen/KeadaanKosong";

export default function Lacak() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6">
      <h1 className="text-2xl font-bold text-tanah">Lacak</h1>
      <KeadaanKosong pesan="Layar lacak belum tersedia. Menyusul di Fase 2." teksAksi="Kembali ke Beranda" ke="/" />
    </main>
  );
}
