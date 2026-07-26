/** Badge status permintaan (§9.7 alur Penerima) — bahasa pill terpadu (K12), sama pola
 *  dengan BadgeStatus slot: 3 nada saja — baik (daun), netral (kabut), buruk (tanah-liat). */

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
  TERBUKA: "bg-daun/15 text-daun",
  TERPENUHI_SEBAGIAN: "bg-kabut/60 text-tanah/70",
  TERPENUHI: "bg-daun/15 text-daun",
  KEDALUWARSA: "bg-tanah-liat/15 text-tanah-liat",
};

export default function BadgePermintaan({ status }: BadgePermintaanProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide ${kelas[status]}`}
    >
      {label[status]}
    </span>
  );
}
