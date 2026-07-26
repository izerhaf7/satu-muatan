/** Badge sumber angka — TERVERIFIKASI vs ASUMSI (§9.9 Panel Asumsi, aturan keras #4). */

import { BadgeCheck, FlaskConical, type LucideIcon } from "lucide-react";

import type { components } from "@/api/client";

type StatusSumber = components["schemas"]["StatusSumber"];

interface BadgeSumberProps {
  status: StatusSumber;
  catatan?: string | null;
}

const label: Record<StatusSumber, string> = {
  TERVERIFIKASI: "Terverifikasi",
  ASUMSI: "Asumsi",
};

const kelas: Record<StatusSumber, string> = {
  TERVERIFIKASI: "bg-daun/15 text-daun",
  ASUMSI: "border border-dashed border-tanah/30 text-tanah/60",
};

const ikon: Record<StatusSumber, LucideIcon> = {
  TERVERIFIKASI: BadgeCheck,
  ASUMSI: FlaskConical,
};

export default function BadgeSumber({ status, catatan }: BadgeSumberProps) {
  const Ikon = ikon[status];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide ${kelas[status]}`}
      title={catatan ?? undefined}
    >
      <Ikon aria-hidden className="h-3 w-3" />
      {label[status]}
    </span>
  );
}
