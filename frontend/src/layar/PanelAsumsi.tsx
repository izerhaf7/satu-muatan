/** Stub Panel Asumsi (§9.9, pembeda utama) — dibangun penuh di Fase 2 (layar-bukti). */

import KeadaanKosong from "@/komponen/KeadaanKosong";

export default function PanelAsumsi() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6">
      <h1 className="text-2xl font-bold text-tanah">Panel Asumsi</h1>
      <KeadaanKosong pesan="Panel asumsi belum tersedia. Menyusul di Fase 2." teksAksi="Kembali ke Beranda" ke="/" />
    </main>
  );
}
