/** Beranda Petani (§9.2 varian) — daftar slot terbuka koperasinya.
 *  Ikut kirim terjadi di Detail Slot (Fase 2), belum di sini. */

import KartuSlot from "@/komponen/KartuSlot";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import Tombol from "@/komponen/Tombol";
import { useDaftarSlot } from "@/hooks/useSlot";

export default function BerandaPetani() {
  const daftarSlot = useDaftarSlot("DIBUKA");

  return (
    <main className="flex flex-1 flex-col gap-6 px-5 py-6 pb-24">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-tanah">Beranda</h1>
        <p className="text-base text-tanah/70">Slot yang sedang dibuka koperasi Anda</p>
      </header>

      <section aria-label="Daftar slot terbuka" className="flex flex-col gap-3">
        {daftarSlot.isLoading && <p className="text-base text-tanah/60">Memuat slot…</p>}
        {daftarSlot.isError && (
          <div className="flex flex-col items-start gap-3 rounded-lg border-2 border-tanah-liat/40 p-4">
            <p className="text-base text-tanah-liat">Gagal memuat daftar slot.</p>
            <Tombol varian="sekunder" onClick={() => daftarSlot.refetch()}>
              Coba lagi
            </Tombol>
          </div>
        )}
        {daftarSlot.data?.length === 0 && (
          <KeadaanKosong pesan="Belum ada slot dibuka. Slot baru akan muncul di sini begitu koperasi membukanya." />
        )}
        {daftarSlot.data?.map((slot) => <KartuSlot key={slot.id} slot={slot} />)}
      </section>
    </main>
  );
}
