/** Badge status permintaan (§9.7 alur Penerima) — palet & pola sama dengan BadgeStatus slot,
 *  tapi untuk StatusPermintaan (skema berbeda, jadi komponen terpisah, bukan mengubah yang lama). */

import type { components } from "@/api/client";

type StatusPermintaan = components["schemas"]["StatusPermintaan"];

interface BadgePermintaanProps {
  status: StatusPermintaan;
}

const label: Record<StatusPermintaan, string> = {
  TERBUKA: "Terbuka",
  TERPENUHI_SEBAGIAN: "Terpenuhi sebagian",
  TERPENUHI: "Terpenuhi",
  KEDALUWARSA: "Kedaluwarsa",
};

const kelas: Record<StatusPermintaan, string> = {
  TERBUKA: "bg-daun text-kertas",
  TERPENUHI_SEBAGIAN: "bg-tanah text-kertas",
  TERPENUHI: "bg-kabut text-tanah",
  KEDALUWARSA: "bg-kabut text-tanah/60",
};

export default function BadgePermintaan({ status }: BadgePermintaanProps) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-sm font-semibold ${kelas[status]}`}>
      {label[status]}
    </span>
  );
}
