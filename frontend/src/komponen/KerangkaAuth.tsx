import type { ReactNode } from "react";
import { ClipboardCheck, Lock, Route, type LucideIcon } from "lucide-react";

import TrukIlustrasi from "../layar/landing/komponen/TrukIlustrasi";
import "./KerangkaAuth.css";

interface KerangkaAuthProps {
  children: ReactNode;
  keterangan: string;
}

const NILAI_UTAMA: { judul: string; keterangan: string; ikon: LucideIcon }[] = [
  {
    judul: "Harga atap terkunci",
    keterangan: "Tidak pernah naik setelah kamu bergabung.",
    ikon: Lock,
  },
  {
    judul: "Bukti mutu terekam",
    keterangan: "Grade, suhu, dan indeks mutu sepanjang jalan.",
    ikon: ClipboardCheck,
  },
  {
    judul: "Satu truk searah",
    keterangan: "Kiriman petani dirombak otomatis jadi satu muatan.",
    ikon: Route,
  },
];

function IdentitasForm({ keterangan }: Pick<KerangkaAuthProps, "keterangan">) {
  return (
    <div className="flex flex-col items-center gap-2 text-center">
      <img src="/ikon-192.png" alt="" className="h-14 w-14 rounded-2xl" />
      <p className="text-subjudul font-extrabold text-tanah">Satu Muatan</p>
      <p className="text-keterangan text-tanah/60">{keterangan}</p>
    </div>
  );
}

export default function KerangkaAuth({ children, keterangan }: KerangkaAuthProps) {
  return (
    <main className="min-h-screen bg-kertas lg:grid lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <aside className="auth-panel hidden overflow-hidden bg-tanah text-kertas lg:flex lg:min-h-screen lg:flex-col lg:justify-center lg:px-10 lg:py-12 xl:px-16">
        <div className="mx-auto flex w-full max-w-xl flex-col">
          <div className="flex items-center gap-3">
            <img src="/ikon-192.png" alt="" className="h-12 w-12 rounded-xl" />
            <p className="text-judul font-extrabold">Satu Muatan</p>
          </div>

          <h1 className="mt-8 max-w-lg text-judul font-extrabold xl:text-display">
            Kiriman lebih pasti, mutu tetap terlihat.
          </h1>

          <div className="mt-8 flex flex-col gap-5">
            {NILAI_UTAMA.map((nilai) => (
              <div key={nilai.judul} className="flex items-start gap-4">
                <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-kertas/10 text-kertas">
                  <nilai.ikon aria-hidden className="h-6 w-6" strokeWidth={2} />
                </span>
                <div className="pt-0.5">
                  <p className="font-bold text-kertas">{nilai.judul}</p>
                  <p className="mt-1 text-keterangan text-kertas/60">{nilai.keterangan}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mx-auto mt-6 w-4/5 max-w-md" aria-hidden="true">
            <TrukIlustrasi />
          </div>

          <div className="angka mt-2 flex flex-wrap justify-center gap-x-4 gap-y-1 text-keterangan tracking-wide text-kertas/40">
            <span>CDD · 2.000 KG</span>
            <span>TERISI 1.200 KG</span>
            <span>RP426/KG</span>
          </div>
        </div>
      </aside>

      <section className="relative flex min-h-screen items-center justify-center overflow-hidden bg-kabut/40 px-5 py-10 lg:px-10 lg:py-12">
        <div aria-hidden className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-daun/5" />
        <div aria-hidden className="absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-tanah/5" />

        <div className="relative z-10 flex w-full max-w-md flex-col gap-8">
          <IdentitasForm keterangan={keterangan} />
          {children}
          <p className="text-center text-keterangan text-tanah/50">Satu Muatan - 2026</p>
        </div>
      </section>
    </main>
  );
}
