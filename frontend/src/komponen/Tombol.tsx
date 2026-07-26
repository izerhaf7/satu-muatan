/** Tombol dasar design system — min-h 48px (target sentuh, spec §10).
 *  Varian: aksi (utama), sekunder (garis), bahaya (tolak/batal), halus (rendah).
 *  Micro-feedback interaksi (K12): transisi ≤150ms, tekan = turun 1px. */

import type { ButtonHTMLAttributes, ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { Loader2 } from "lucide-react";

export type VarianTombol = "aksi" | "sekunder" | "bahaya" | "halus";

interface TombolProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  varian?: VarianTombol;
  children: ReactNode;
  /** Ikon lucide opsional di kiri teks. */
  ikon?: LucideIcon;
  /** Saat true: spinner menggantikan ikon, tombol nonaktif. */
  sedangProses?: boolean;
}

export const kelasDasarTombol =
  "inline-flex min-h-sentuh min-w-sentuh items-center justify-center gap-2 rounded-lg px-5 " +
  "text-base font-semibold transition-all duration-cepat select-none " +
  "active:translate-y-px disabled:cursor-not-allowed disabled:active:translate-y-0";

export const kelasVarianTombol: Record<VarianTombol, string> = {
  aksi: "bg-daun text-kertas shadow-lembut hover:bg-daun/90 disabled:bg-kabut disabled:text-tanah/40 disabled:shadow-none",
  sekunder:
    "bg-transparent text-tanah border-2 border-tanah hover:bg-tanah/5 disabled:border-kabut disabled:text-tanah/40",
  bahaya: "bg-tanah-liat text-kertas shadow-lembut hover:bg-tanah-liat/90 disabled:bg-kabut disabled:text-tanah/40 disabled:shadow-none",
  halus: "bg-tanah/5 text-tanah hover:bg-tanah/10 disabled:text-tanah/40",
};

export default function Tombol({
  varian = "aksi",
  className = "",
  children,
  ikon: Ikon,
  sedangProses = false,
  disabled,
  ...props
}: TombolProps) {
  return (
    <button
      className={`${kelasDasarTombol} ${kelasVarianTombol[varian]} ${className}`}
      disabled={disabled || sedangProses}
      {...props}
    >
      {sedangProses ? (
        <Loader2 aria-hidden className="h-5 w-5 animate-spin" />
      ) : (
        Ikon && <Ikon aria-hidden className="h-5 w-5" strokeWidth={2.25} />
      )}
      {children}
    </button>
  );
}
