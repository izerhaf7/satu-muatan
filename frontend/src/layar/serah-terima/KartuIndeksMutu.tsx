/** Penilaian mutu SISTEM untuk satu lot (K14).
 *
 *  Inilah yang hilang sebelumnya: penerima memutuskan terima/tolak tanpa pernah
 *  melihat angka apa pun, lalu baru diberi tahu hasilnya setelah keputusannya
 *  terkirim. Kartu ini membalik urutan itu.
 *
 *  Angkanya murni dari data terpantau — sisa umur simpan (telemetri suhu) dan
 *  ketepatan waktu tempuh. Grade tiba sengaja tidak ikut supaya penerima tidak
 *  bisa menggerakkan penilaian yang menjadi dasar haknya menolak. */

import { ShieldCheck, ShieldAlert, Thermometer, Timer } from "lucide-react";

import type { components } from "@/api/client";

type IndeksMutuOut = components["schemas"]["IndeksMutuOut"];

interface KartuIndeksMutuProps {
  mutu: IndeksMutuOut;
}

/** Tiga nada palet (K12) — tidak menambah warna di luar palet 5. */
function nada(indeks: number): { teks: string; latar: string; batas: string } {
  if (indeks >= 80) return { teks: "text-daun", latar: "bg-daun/5", batas: "border-daun/40" };
  if (indeks >= 50) return { teks: "text-tanah", latar: "bg-kabut/30", batas: "border-kabut" };
  return { teks: "text-tanah-liat", latar: "bg-tanah-liat/5", batas: "border-tanah-liat/40" };
}

export default function KartuIndeksMutu({ mutu }: KartuIndeksMutuProps) {
  const warna = nada(mutu.indeks_mutu);
  const Ikon = mutu.boleh_tolak ? ShieldAlert : ShieldCheck;

  return (
    <section
      aria-label="Penilaian mutu sistem"
      className={`flex flex-col gap-3 rounded-xl border-2 p-4 ${warna.batas} ${warna.latar}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-0.5">
          <p className="text-keterangan font-bold uppercase tracking-wide text-tanah/55">Indeks mutu sistem</p>
          <p className="text-keterangan text-tanah/60">Dihitung dari data perjalanan, bukan penilaian mata</p>
        </div>
        <Ikon aria-hidden className={`h-6 w-6 shrink-0 ${warna.teks}`} strokeWidth={2.25} />
      </div>

      <div className="flex items-end gap-3">
        <p className={`angka text-4xl font-bold leading-none ${warna.teks}`}>{mutu.indeks_mutu}</p>
        <p className="pb-1 text-base text-tanah/70">
          dari 100 · penurunan <span className="angka font-semibold text-tanah">{mutu.penurunan_mutu_persen}%</span>
        </p>
      </div>

      <div
        className="h-2 w-full overflow-hidden rounded-full bg-tanah/10"
        role="img"
        aria-label={`Indeks mutu ${mutu.indeks_mutu} dari 100`}
      >
        <div
          className={`h-full rounded-full ${mutu.indeks_mutu >= 80 ? "bg-daun" : mutu.indeks_mutu >= 50 ? "bg-tanah/50" : "bg-tanah-liat"}`}
          style={{ width: `${mutu.indeks_mutu}%` }}
        />
      </div>

      <div className="grid grid-cols-2 gap-2 border-t border-tanah/10 pt-3">
        <Komponen ikon={Thermometer} label="Umur simpan" nilai={mutu.skor_umur_simpan} />
        <Komponen ikon={Timer} label="Ketepatan waktu" nilai={mutu.skor_transit} />
      </div>

      <p className="text-keterangan leading-relaxed text-tanah/70">{mutu.alasan_boleh_tolak}</p>
    </section>
  );
}

function Komponen({
  ikon: Ikon,
  label,
  nilai,
}: {
  ikon: typeof Thermometer;
  label: string;
  nilai: number;
}) {
  return (
    <div className="flex items-center gap-2">
      <Ikon aria-hidden className="h-4 w-4 shrink-0 text-tanah/45" strokeWidth={2.25} />
      <div className="min-w-0">
        <p className="angka text-base font-semibold text-tanah">{nilai}</p>
        <p className="truncate text-keterangan text-tanah/55">{label}</p>
      </div>
    </div>
  );
}
