/** Band angka full-bleed (bg-tanah) — tiga statistik terungkap saat discroll.
 *  (a) memakai AngkaCountUp (komponen bersama, teksnya sengaja hardcode text-tanah
 *  di atas kertas — makanya tiap kartu di sini dibungkus kertas, bukan dipaksa
 *  warna lain di atas latar gelap). Semua angka dari K2 — tidak ada yang direka. */

import AngkaCountUp from "@/komponen/AngkaCountUp";

import { kelasScrollReveal, useTampilSaatScroll } from "../useTampilSaatScroll";

export default function AngkaBand() {
  const { ref, terlihat } = useTampilSaatScroll<HTMLDivElement>();

  return (
    <section className="bg-tanah px-5 py-16 text-kertas sm:py-20">
      <div className="mx-auto flex max-w-5xl flex-col gap-10">
        <div className={`mx-auto max-w-xl text-center ${kelasScrollReveal(terlihat)}`}>
          <p className="text-keterangan font-semibold uppercase tracking-wide text-kertas/60">
            Angka yang bicara
          </p>
          <h2 className="mt-2 text-judul text-kertas">Satu slot, ongkos yang jauh lebih murah</h2>
        </div>

        <div ref={ref} className="grid gap-5 sm:grid-cols-3">
          <div
            className={`kartu-tonjol flex flex-col items-center gap-2 p-6 text-center ${kelasScrollReveal(terlihat)}`}
          >
            <AngkaCountUp nilai={terlihat ? 388 : 1007} satuan="/kg" ukuran="besar" />
            <p className="text-keterangan text-tanah/60">4 petani bergabung dalam satu slot</p>
          </div>

          <div
            className={`kartu-tonjol flex flex-col items-center gap-2 p-6 text-center ${kelasScrollReveal(terlihat)}`}
            style={{ transitionDelay: terlihat ? "120ms" : "0ms" }}
          >
            <p className="angka text-4xl font-bold text-tanah">63–75%</p>
            <p className="text-keterangan text-tanah/60">penurunan ongkos per kg dibanding kirim sendirian</p>
          </div>

          <div
            className={`kartu-tonjol flex flex-col items-center gap-2 p-6 text-center ${kelasScrollReveal(terlihat)}`}
            style={{ transitionDelay: terlihat ? "240ms" : "0ms" }}
          >
            <p className="angka text-4xl font-bold text-tanah">70 km</p>
            <p className="text-keterangan text-tanah/60">rute nyata Garut → Bandung yang dipakai demo</p>
          </div>
        </div>
      </div>
    </section>
  );
}
