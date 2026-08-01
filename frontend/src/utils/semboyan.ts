/** Empat semboyan produk (spec v2 §7) — KATA & URUTAN WAJIB sama persis di
 *  Dashboard Dampak dan Landing (§7.3). Jangan tulis ulang di tempat lain;
 *  jangan bikin versi semboyan lain. */

export const SEMBOYAN = [
  { kunci: "biaya_logistik", label: "Menekan biaya logistik" },
  { kunci: "emisi", label: "Menurunkan emisi" },
  { kunci: "transparansi_perjalanan", label: "Transparansi perjalanan" },
  { kunci: "keamanan_pangan", label: "Keamanan pangan" },
] as const;

export type KunciSemboyan = (typeof SEMBOYAN)[number]["kunci"];
