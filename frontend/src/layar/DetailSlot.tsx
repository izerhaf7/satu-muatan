/** Stub Detail Slot (§9.4) — layar utama demo, dibangun penuh di Fase 2.
 *  Rute dipasang di Fase 1 agar navigasi dari Beranda tidak 404. */

import { useParams } from "react-router-dom";

import KeadaanKosong from "@/komponen/KeadaanKosong";

export default function DetailSlot() {
  const { id } = useParams();

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6">
      <h1 className="text-2xl font-bold text-tanah">Detail Slot</h1>
      <KeadaanKosong
        pesan={`Layar detail slot ${id ?? ""} belum tersedia. Menyusul di Fase 2.`}
        teksAksi="Kembali ke Beranda"
        ke="/"
      />
    </main>
  );
}
