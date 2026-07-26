/** Bar isi kapasitas slot (§9.2, §9.4 butir 4).
 *  Murni presentasi: `varian` dikendalikan pemanggil (mis. layar Detail Slot Fase 2
 *  yang tahu batas tier dari `rencana_saat_ini`) — komponen ini tidak menyimpan
 *  angka/aturan bisnis apa pun (Aturan keras #1). */

import { formatAngka } from "@/utils/format";

export type VarianKapasitas = "normal" | "mendekati-batas";

interface BarKapasitasProps {
  volumeKg: number;
  kapasitasKg: number | null;
  varian?: VarianKapasitas;
  className?: string;
}

const kelasWarna: Record<VarianKapasitas, string> = {
  normal: "bg-daun",
  "mendekati-batas": "bg-tanah-liat",
};

export default function BarKapasitas({
  volumeKg,
  kapasitasKg,
  varian = "normal",
  className = "",
}: BarKapasitasProps) {
  const persen = kapasitasKg && kapasitasKg > 0 ? Math.min(100, (volumeKg / kapasitasKg) * 100) : 0;
  const label = kapasitasKg
    ? `Terisi ${formatAngka(volumeKg)} dari ${formatAngka(kapasitasKg)} kg`
    : `${formatAngka(volumeKg)} kg terkumpul`;

  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-kabut/70" role="img" aria-label={label}>
        <div
          className={`h-full rounded-full transition-[width] duration-500 ${kelasWarna[varian]}`}
          style={{ width: `${persen}%` }}
        />
      </div>
      <p className="angka text-keterangan text-tanah/70">
        {kapasitasKg ? `${formatAngka(volumeKg)} / ${formatAngka(kapasitasKg)} kg` : `${formatAngka(volumeKg)} kg`}
      </p>
    </div>
  );
}
