/** #cara-kerja — tiga langkah, target smooth-scroll dari CTA sekunder hero. */

import { BadgeCheck, Users, Warehouse } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { kelasScrollReveal, useTampilSaatScroll } from "../useTampilSaatScroll";

interface Langkah {
  ikon: LucideIcon;
  judul: string;
  keterangan: string;
}

const LANGKAH: Langkah[] = [
  {
    ikon: Warehouse,
    judul: "Titik kumpul buka slot kirim",
    keterangan: "Petugas titik kumpul membuka slot untuk satu tujuan dan memilih armada yang dipakai.",
  },
  {
    ikon: Users,
    judul: "Petani ikut kirim, harga atap langsung terkunci",
    keterangan: "Setiap petani yang bergabung langsung melihat harga atapnya — harga itu tidak akan naik lagi.",
  },
  {
    ikon: BadgeCheck,
    judul: "Serah terima berbukti foto & waktu",
    keterangan: "Muat dan bongkar difoto serta dicap waktu, jadi bukti mutu yang bisa ditelusuri kapan saja.",
  },
];

export default function CaraKerja() {
  const { ref, terlihat } = useTampilSaatScroll<HTMLDivElement>();

  return (
    <section id="cara-kerja" className="mx-auto max-w-5xl scroll-mt-20 px-5 py-16 sm:py-20">
      <div className="mx-auto max-w-xl text-center">
        <p className="text-keterangan font-semibold uppercase tracking-wide text-daun">Cara kerja</p>
        <h2 className="mt-2 text-judul text-tanah">Tiga langkah, dari desa sampai serah terima</h2>
      </div>

      <div ref={ref} className="mt-10 grid gap-5 sm:grid-cols-3">
        {LANGKAH.map((langkah, i) => (
          <div
            key={langkah.judul}
            className={`kartu-tonjol flex flex-col gap-3 p-6 ${kelasScrollReveal(terlihat)}`}
            style={{ transitionDelay: terlihat ? `${i * 100}ms` : "0ms" }}
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-daun/10 text-daun">
              <langkah.ikon aria-hidden className="h-6 w-6" strokeWidth={2} />
            </div>
            <p className="text-keterangan font-bold uppercase tracking-wide text-daun/70">Langkah {i + 1}</p>
            <h3 className="text-subjudul text-tanah">{langkah.judul}</h3>
            <p className="text-base text-tanah/70">{langkah.keterangan}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
