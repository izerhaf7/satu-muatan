/** Badge status slot (§9.2–§9.4). */

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
  DIBUKA: "bg-daun text-kertas",
  TERKUNCI: "bg-tanah-liat text-kertas",
  DIMUAT: "bg-tanah text-kertas",
  JALAN: "bg-tanah text-kertas",
  SELESAI: "bg-kabut text-tanah",
  BATAL: "bg-kabut text-tanah/60",
};

export default function BadgeStatus({ status }: BadgeStatusProps) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-sm font-semibold ${kelas[status]}`}>
      {label[status]}
    </span>
  );
}
