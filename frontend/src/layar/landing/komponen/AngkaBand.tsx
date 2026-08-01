/** Band semboyan full-bleed (bg-tanah) — EMPAT SEMBOYAN produk (spec v2 §7.3),
 *  kata & urutan PERSIS sama dengan Dashboard Dampak (lihat utils/semboyan.ts).
 *  Angka contoh dari skenario demo (§7.1) — dihitung ulang live oleh mesin di
 *  dalam aplikasi; di sini disalin sebagai janji produk, bukan klaim acak. */

import { kelasScrollReveal, useTampilSaatScroll } from "../useTampilSaatScroll";
import { SEMBOYAN } from "@/utils/semboyan";

/** Angka contoh per semboyan (urutan mengikuti SEMBOYAN). */
const CONTOH: { angka: string; keterangan: string }[] = [
  { angka: "−68%", keterangan: "Rp1.300 → Rp420 per kg pada muatan penuh" },
  { angka: "63 kg CO₂e", keterangan: "252 truk-km tidak jadi ditempuh" },
  { angka: "178 / 181 menit", keterangan: "Waktu tempuh vs ambang rute, terekam" },
  { angka: "71%", keterangan: "Sisa umur simpan saat kiriman tiba" },
];

export default function AngkaBand() {
  const { ref, terlihat } = useTampilSaatScroll<HTMLDivElement>();

  return (
    <section className="bg-tanah px-5 py-16 text-kertas sm:py-20">
      <div className="mx-auto flex max-w-5xl flex-col gap-10">
        <div className={`mx-auto max-w-xl text-center ${kelasScrollReveal(terlihat)}`}>
          <p className="text-keterangan font-semibold uppercase tracking-wide text-kertas/60">
            Angka yang bicara
          </p>
          <h2 className="mt-2 text-judul text-kertas">Satu muatan, empat bukti</h2>
        </div>

        <div ref={ref} className="grid gap-5 grid-cols-2 lg:grid-cols-4">
          {SEMBOYAN.map((semboyan, i) => (
            <div
              key={semboyan.kunci}
              className={`kartu-tonjol flex flex-col items-center gap-2 p-5 text-center ${kelasScrollReveal(terlihat)}`}
              style={{ transitionDelay: terlihat ? `${i * 100}ms` : "0ms" }}
            >
              <p className="text-keterangan font-semibold uppercase tracking-wide text-daun">{semboyan.label}</p>
              <p className="angka text-3xl font-bold text-tanah">{CONTOH[i].angka}</p>
              <p className="text-keterangan text-tanah/60">{CONTOH[i].keterangan}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
