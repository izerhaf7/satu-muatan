/** Beranda Petani (§9.2 varian + v2 §3.4) — sapaan, CTA Kirim Panen (alur baru:
 *  sistem yang mencocokkan), dan daftar muatan titik kumpulnya.
 *
 *  K14: muatan yang sudah ditutup TIDAK lagi lenyap dari layar ini. Sebelumnya
 *  daftar disaring DIBUKA saja, jadi begitu muatan dikunci petani kehilangan
 *  jejaknya sampai ia ingat membuka Riwayat. */

import { PackagePlus } from "lucide-react";

import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { SkeletonKartu } from "@/komponen/Skeleton";
import TombolTautan from "@/komponen/TombolTautan";
import { useDaftarSlot } from "@/hooks/useSlot";
import { useAuthStore } from "@/stores/authStore";

import KartuSlotDaftar from "./KartuSlotDaftar";

export default function BerandaPetani() {
  const pengguna = useAuthStore((s) => s.pengguna);
  const daftarSlot = useDaftarSlot();

  const berjalan = daftarSlot.data?.filter((s) => s.status === "DIBUKA") ?? [];
  const selesai = daftarSlot.data?.filter((s) => s.status !== "DIBUKA") ?? [];

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1 pt-1">
        <p className="text-keterangan font-bold uppercase tracking-wide text-daun">Beranda</p>
        <h1 className="text-judul text-tanah">Halo, {pengguna?.nama ?? "Kamu"}</h1>
        <p className="text-base text-tanah/70">Muatan tempat panenmu ikut berangkat</p>
      </header>

      <TombolTautan to="/kirim" ikon={PackagePlus} varian="aksi" className="w-full">
        Kirim Panen
      </TombolTautan>

      {daftarSlot.isLoading && <SkeletonKartu />}
      {daftarSlot.isError && (
        <KartuGalat pesan="Gagal memuat daftar muatan." onCobaLagi={() => daftarSlot.refetch()} />
      )}
      {daftarSlot.data?.length === 0 && (
        <KeadaanKosong pesan="Belum ada muatan. Kirim panenmu dan sistem akan mencarikan muatan searah — atau membuka yang baru." />
      )}

      {berjalan.length > 0 && (
        <section aria-label="Muatan berjalan" className="flex flex-col gap-3">
          <h2 className="text-subjudul text-tanah">Sedang berjalan</h2>
          <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2 lg:items-start">
            {berjalan.map((slot) => (
              <KartuSlotDaftar key={slot.id} slot={slot} />
            ))}
          </div>
        </section>
      )}

      {selesai.length > 0 && (
        <section aria-label="Muatan sudah ditutup" className="flex flex-col gap-3">
          <h2 className="text-subjudul text-tanah">Sudah ditutup</h2>
          <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2 lg:items-start">
            {selesai.map((slot) => (
              <KartuSlotDaftar key={slot.id} slot={slot} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
