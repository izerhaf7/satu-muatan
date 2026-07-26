/** Stub Serah Terima (§9.7, peran Penerima) — dibangun penuh di Fase 2 (layar-operasi). */

import KeadaanKosong from "@/komponen/KeadaanKosong";

export default function SerahTerima() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6">
      <h1 className="text-2xl font-bold text-tanah">Serah Terima</h1>
      <KeadaanKosong pesan="Layar serah terima belum tersedia. Menyusul di Fase 2." teksAksi="Kembali ke Beranda" ke="/" />
    </main>
  );
}
