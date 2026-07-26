/** Grid fitur unggulan — 2 kolom mobile, 3 kolom desktop, kartu-datar. */

import { Leaf, Lock, Scale, Smartphone, SlidersHorizontal, TrendingDown } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { kelasScrollReveal, useTampilSaatScroll } from "../useTampilSaatScroll";

interface Fitur {
  ikon: LucideIcon;
  judul: string;
  keterangan: string;
}

const FITUR: Fitur[] = [
  {
    ikon: Lock,
    judul: "Harga atap terkunci",
    keterangan: "Begitu petani bergabung, harga itu tidak pernah naik lagi — walau slotnya penuh.",
  },
  {
    ikon: TrendingDown,
    judul: "Harga berjalan live",
    keterangan: "Makin banyak yang ikut satu slot, harga per kilogram makin turun secara langsung.",
  },
  {
    ikon: Scale,
    judul: "Atribusi mutu jujur",
    keterangan: "Kalau sumber mutu suatu kiriman belum terbukti, sistem berani bilang “tidak terbukti”.",
  },
  {
    ikon: SlidersHorizontal,
    judul: "Panel Asumsi transparan",
    keterangan: "Semua koefisien di balik perhitungan bisa dilihat dan ditelusuri, bukan kotak hitam.",
  },
  {
    ikon: Leaf,
    judul: "Dashboard Dampak",
    keterangan: "Pantau penghematan, jarak truk yang dihemat, dan emisi yang tercatat tiap bulan.",
  },
  {
    ikon: Smartphone,
    judul: "Terpasang seperti aplikasi",
    keterangan: "Bisa dipasang ke layar utama HP (PWA) dan tetap jalan walau koneksi lemah.",
  },
];

export default function FiturUnggulan() {
  const { ref, terlihat } = useTampilSaatScroll<HTMLDivElement>();

  return (
    <section className="mx-auto max-w-5xl px-5 py-16 sm:py-20">
      <div className="mx-auto max-w-xl text-center">
        <p className="text-keterangan font-semibold uppercase tracking-wide text-daun">Fitur unggulan</p>
        <h2 className="mt-2 text-judul text-tanah">Dibangun supaya angka dan mutu bisa dipercaya</h2>
      </div>

      <div ref={ref} className="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-3 sm:gap-5">
        {FITUR.map((fitur, i) => (
          <div
            key={fitur.judul}
            className={`kartu-datar flex flex-col gap-2.5 p-4 sm:p-5 ${kelasScrollReveal(terlihat)}`}
            style={{ transitionDelay: terlihat ? `${(i % 3) * 90}ms` : "0ms" }}
          >
            <fitur.ikon aria-hidden className="h-6 w-6 text-daun" strokeWidth={2} />
            <h3 className="text-base font-bold text-tanah">{fitur.judul}</h3>
            <p className="text-keterangan text-tanah/60">{fitur.keterangan}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
