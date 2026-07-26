/** Badge status slot (§9.2–§9.4). Bahasa pill terpadu (K12): 3 nada saja —
 *  baik (daun), netral (kabut), buruk (tanah-liat) — teks yang membedakan makna. */

import type { components } from "@/api/client";

type StatusSlot = components["schemas"]["StatusSlot"];

interface BadgeStatusProps {
  status: StatusSlot;
}

const label: Record<StatusSlot, string> = {
  DIBUKA: "Dibuka",
  TERKUNCI: "Terkunci",
  DIMUAT: "Dimuat",
  JALAN: "Jalan",
  SELESAI: "Selesai",
  BATAL: "Batal",
};

const kelas: Record<StatusSlot, string> = {
  DIBUKA: "bg-daun/15 text-daun",
  TERKUNCI: "bg-tanah-liat/15 text-tanah-liat",
  DIMUAT: "bg-kabut/60 text-tanah/60",
  JALAN: "bg-kabut/60 text-tanah/60",
  SELESAI: "bg-daun/15 text-daun",
  BATAL: "bg-tanah-liat/15 text-tanah-liat",
};

export default function BadgeStatus({ status }: BadgeStatusProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide ${kelas[status]}`}
    >
      {label[status]}
    </span>
  );
}
