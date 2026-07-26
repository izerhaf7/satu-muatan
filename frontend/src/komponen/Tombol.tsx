/** Tombol dasar design system — min-h 48px (target sentuh, spec §10).
 *  Varian: aksi (utama), sekunder (garis), bahaya (tolak/batal). */

import type { ButtonHTMLAttributes, ReactNode } from "react";

export type VarianTombol = "aksi" | "sekunder" | "bahaya";

interface TombolProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  varian?: VarianTombol;
  children: ReactNode;
}

const kelasVarian: Record<VarianTombol, string> = {
  aksi: "bg-daun text-kertas disabled:bg-kabut disabled:text-tanah/40",
  sekunder: "bg-transparent text-tanah border-2 border-tanah disabled:border-kabut disabled:text-tanah/40",
  bahaya: "bg-tanah-liat text-kertas disabled:bg-kabut disabled:text-tanah/40",
};

export default function Tombol({ varian = "aksi", className = "", children, ...props }: TombolProps) {
  return (
    <button
      className={`inline-flex min-h-sentuh min-w-sentuh items-center justify-center gap-2 rounded-md px-5 text-base font-semibold disabled:cursor-not-allowed ${kelasVarian[varian]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
