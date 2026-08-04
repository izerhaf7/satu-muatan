/** Data navigasi bersama untuk NavBawah (ponsel) dan NavSamping (desktop ≥lg).
 *  Satu sumber kebenaran: item nav per peran + label peran untuk kartu akun. */

import { BarChart3, Home, ListChecks, PackageCheck, PackagePlus, Search, SlidersHorizontal } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface ItemNav {
  ke: string;
  label: string;
  ikon: LucideIcon;
}

export const NAV_PER_PERAN: Record<string, ItemNav[]> = {
  // K13: petugas = driver Satu Muatan. Dia tidak "membuka muatan" — muatan
  // ditugaskan sistem kepadanya; dia mengecek komoditas petani lalu membawanya.
  // K14: petugas BUKAN pengirim. Menu Kirim Panen dicabut — dia menjemput dan
  // mengantar panen orang lain, bukan menyetorkan panennya sendiri.
  PETUGAS: [
    { ke: "/beranda", label: "Muatan", ikon: Home },
    { ke: "/dampak", label: "Dampak", ikon: BarChart3 },
    { ke: "/asumsi", label: "Asumsi", ikon: SlidersHorizontal },
  ],
  PETANI: [
    { ke: "/beranda", label: "Beranda", ikon: Home },
    { ke: "/kirim", label: "Kirim Panen", ikon: PackagePlus },
    { ke: "/riwayat", label: "Riwayat", ikon: ListChecks },
  ],
  // K13: penerima MURNI menerima — melacak resi, melihat data perjalanan, dan
  // menyerahterimakan. Tidak ada lagi memesan atau membuka muatan.
  PENERIMA: [
    { ke: "/beranda", label: "Beranda", ikon: Home },
    { ke: "/lacak-resi", label: "Lacak Resi", ikon: Search },
    { ke: "/serah-terima", label: "Serah Terima", ikon: PackageCheck },
  ],
};

export const LABEL_PERAN: Record<string, string> = {
  PETUGAS: "Petugas Satu Muatan",
  PETANI: "Petani",
  PENERIMA: "Penerima",
};
