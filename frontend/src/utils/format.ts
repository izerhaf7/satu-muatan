/** Util format angka & tanggal — dipakai lintas layar & komponen.
 *  Tanpa angka bisnis di sini, murni fungsi presentasi (Aturan keras #1). */

/** Format angka dengan pemisah ribuan gaya Indonesia (mis. 12345 -> "12.345"). */
export function formatAngka(nilai: number): string {
  return new Intl.NumberFormat("id-ID").format(nilai);
}

/** Format nilai rupiah dengan awalan "Rp" (mis. 1500 -> "Rp1.500"). */
export function formatRupiah(nilai: number): string {
  return `Rp${formatAngka(Math.round(nilai))}`;
}

/** Format tanggal ISO (yyyy-mm-dd) jadi "5 Agu 2026". */
export function formatTanggal(tanggal: string): string {
  return new Date(tanggal).toLocaleDateString("id-ID", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

/** Kunci bulan berjalan dalam format "YYYY-MM", dipakai mencocokkan DampakBulananOut.bulan. */
export function bulanSaatIni(): string {
  const sekarang = new Date();
  return `${sekarang.getFullYear()}-${String(sekarang.getMonth() + 1).padStart(2, "0")}`;
}

/** Format kunci bulan "YYYY-MM" jadi label "Juli 2026". */
export function formatBulan(bulan: string): string {
  const [tahun, bulanKe] = bulan.split("-").map(Number);
  if (!tahun || !bulanKe) return bulan;
  return new Date(tahun, bulanKe - 1, 1).toLocaleDateString("id-ID", {
    month: "long",
    year: "numeric",
  });
}
