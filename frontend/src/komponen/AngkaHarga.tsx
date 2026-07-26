/** Angka harga — objek terpenting seluruh aplikasi (spec §10).
 *  Monospace, tabular-nums wajib. TANPA animasi di Fase 1 — count-up harga berjalan
 *  hanya boleh dipasang di layar Detail Slot (§9.4), Fase 2. */

import { formatRupiah } from "@/utils/format";

export type UkuranAngkaHarga = "kecil" | "sedang" | "besar";

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
};

export default function AngkaHarga({ nilai, ukuran = "sedang", satuan, className = "" }: AngkaHargaProps) {
  return (
    <span className={`angka font-bold text-tanah ${kelasUkuran[ukuran]} ${className}`}>
      {nilai === null ? "—" : formatRupiah(nilai)}
      {satuan && nilai !== null && <span className="ml-1 text-base font-normal text-tanah/70">{satuan}</span>}
    </span>
  );
}
