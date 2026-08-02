/** Data navigasi bersama untuk NavBawah (ponsel) dan NavSamping (desktop ≥lg).
 *  Satu sumber kebenaran: item nav per peran + label peran untuk kartu akun. */

import { BarChart3, ClipboardList, Home, ListChecks, PackageCheck, PackagePlus, SlidersHorizontal } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface ItemNav {
  ke: string;
  label: string;
  ikon: LucideIcon;
}

export const NAV_PER_PERAN: Record<string, ItemNav[]> = {
  PETUGAS: [
    { ke: "/beranda", label: "Beranda", ikon: Home },
    { ke: "/kirim", label: "Kirim", ikon: PackagePlus },
    { ke: "/dampak", label: "Dampak", ikon: BarChart3 },
    { ke: "/asumsi", label: "Asumsi", ikon: SlidersHorizontal },
  ],
  PETANI: [
    { ke: "/beranda", label: "Beranda", ikon: Home },
    { ke: "/kirim", label: "Kirim", ikon: PackagePlus },
    { ke: "/riwayat", label: "Riwayat", ikon: ListChecks },
  ],
  PENERIMA: [
    { ke: "/beranda", label: "Beranda", ikon: Home },
    { ke: "/permintaan", label: "Permintaan", ikon: ClipboardList },
    { ke: "/serah-terima", label: "Serah Terima", ikon: PackageCheck },
  ],
};

export const LABEL_PERAN: Record<string, string> = {
  PETUGAS: "Petugas Titik Kumpul",
  PETANI: "Petani",
  PENERIMA: "Dapur Penerima",
};
