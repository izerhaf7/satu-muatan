/** Beranda Petani (§9.2 varian) — sapaan + daftar slot terbuka titik kumpulnya.
 *  Ikut kirim terjadi di Detail Slot, belum di sini. Data/hook sama persis dengan
 *  sebelum rombakan visual (§K12) — hanya bahasa tampilan yang berubah. */

import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { SkeletonKartu } from "@/komponen/Skeleton";
import { useDaftarSlot } from "@/hooks/useSlot";
import { useAuthStore } from "@/stores/authStore";

import KartuSlotDaftar from "./KartuSlotDaftar";

export default function BerandaPetani() {
  const pengguna = useAuthStore((s) => s.pengguna);
  const daftarSlot = useDaftarSlot("DIBUKA");

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1 pt-1">
        <p className="text-keterangan font-bold uppercase tracking-wide text-daun">Beranda</p>
        <h1 className="text-judul text-tanah">Halo, {pengguna?.nama ?? "Kamu"}</h1>
        <p className="text-base text-tanah/70">Slot yang sedang dibuka titik kumpul kamu</p>
      </header>

      <section aria-label="Slot terbuka" className="flex flex-col gap-3 lg:grid lg:grid-cols-2 lg:items-start">
        {daftarSlot.isLoading && <SkeletonKartu />}
        {daftarSlot.isError && (
          <KartuGalat pesan="Gagal memuat daftar slot." onCobaLagi={() => daftarSlot.refetch()} />
        )}
        {daftarSlot.data?.length === 0 && (
          <KeadaanKosong pesan="Belum ada slot dibuka. Slot baru akan muncul di sini begitu titik kumpul membukanya." />
        )}
        {daftarSlot.data?.map((slot) => <KartuSlotDaftar key={slot.id} slot={slot} />)}
      </section>
    </div>
  );
}
