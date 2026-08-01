/** CTA penutup — kartu-hero terpusat, ajakan terakhir sebelum footer. */

import TombolTautan from "@/komponen/TombolTautan";

import { kelasScrollReveal, useTampilSaatScroll } from "../useTampilSaatScroll";

export default function CtaPenutup() {
  const { ref, terlihat } = useTampilSaatScroll<HTMLDivElement>();

  return (
    <section className="mx-auto max-w-5xl px-5 py-16 sm:py-20">
      <div
        ref={ref}
        className={`kartu-hero flex flex-col items-center gap-5 px-6 py-14 text-center sm:px-12 ${kelasScrollReveal(terlihat)}`}
      >
        <h2 className="text-judul text-kertas">Siap mengirim bersama?</h2>
        <p className="max-w-md text-base text-kertas/85">
          Masuk sebagai petugas, petani, atau penerima — coba langsung akun demo tanpa perlu daftar.
        </p>
        <TombolTautan to="/masuk" varian="sekunder" className="!border-kertas !text-kertas hover:!bg-kertas/10">
          Masuk
        </TombolTautan>
      </div>
    </section>
  );
}
