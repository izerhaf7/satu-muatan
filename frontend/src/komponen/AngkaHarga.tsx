/** Angka harga — objek terpenting seluruh aplikasi (spec §10).
 *  Monospace, tabular-nums wajib. Statis (tanpa animasi) — untuk harga atap terkunci
 *  dan tempat lain yang tidak butuh count-up. Count-up harga berjalan sudah ada sejak
 *  Fase 2 lewat AngkaCountUp (§9.4 Detail Slot); JANGAN pasang animasi di sini. */

import { formatRupiah } from "@/utils/format";

export type UkuranAngkaHarga = "kecil" | "sedang" | "besar" | "raksasa";

interface AngkaHargaProps {
  nilai: number | null;
  ukuran?: UkuranAngkaHarga;
  satuan?: string;
  className?: string;
}

const kelasUkuran: Record<UkuranAngkaHarga, string> = {
  kecil: "text-lg",
  sedang: "text-2xl",
  besar: "text-4xl",
  raksasa: "text-display",
};

export default function AngkaHarga({ nilai, ukuran = "sedang", satuan, className = "" }: AngkaHargaProps) {
  return (
    <span className={`angka font-bold text-tanah ${kelasUkuran[ukuran]} ${className}`}>
      {nilai === null ? "—" : formatRupiah(nilai)}
      {satuan && nilai !== null && <span className="ml-1 text-base font-normal text-tanah/70">{satuan}</span>}
    </span>
  );
}
