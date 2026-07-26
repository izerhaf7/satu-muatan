/** Badge sumber angka — TERVERIFIKASI vs ASUMSI (§9.9 Panel Asumsi, aturan keras #4). */

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
  TERVERIFIKASI: "border-daun text-daun",
  ASUMSI: "border-tanah-liat text-tanah-liat",
};

export default function BadgeSumber({ status, catatan }: BadgeSumberProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border-2 px-2 py-0.5 text-sm font-medium ${kelas[status]}`}
      title={catatan ?? undefined}
    >
      {label[status]}
    </span>
  );
}
