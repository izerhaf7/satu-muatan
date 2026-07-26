/** Timeline vertikal Lacak (§9.6): Dipesan -> Dimuat -> Jalan -> Tiba, tahap saat ini disorot
 *  dengan ring, tahap tercapai berupa lingkaran daun terisi berikon, sisanya redup. */

import { ClipboardList, MapPinCheck, PackageCheck, Truck, type LucideIcon } from "lucide-react";

import type { components } from "@/api/client";

type TimelineOut = components["schemas"]["TimelineOut"];

interface TimelineLacakProps {
  timeline: TimelineOut;
  className?: string;
}

function formatWaktu(waktu: string): string {
  return new Date(waktu).toLocaleString("id-ID", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const TAHAP: { kunci: keyof TimelineOut; label: string; ikon: LucideIcon }[] = [
  { kunci: "dipesan", label: "Dipesan", ikon: ClipboardList },
  { kunci: "dimuat", label: "Dimuat", ikon: PackageCheck },
  { kunci: "berangkat", label: "Jalan", ikon: Truck },
  { kunci: "tiba", label: "Tiba", ikon: MapPinCheck },
];

export default function TimelineLacak({ timeline, className = "" }: TimelineLacakProps) {
  const indeksSaatIni = TAHAP.reduce((acc, tahap, idx) => (timeline[tahap.kunci] ? idx : acc), -1);

  return (
    <ol className={`flex flex-col ${className}`}>
      {TAHAP.map((tahap, idx) => {
        const waktu = timeline[tahap.kunci];
        const tercapai = idx <= indeksSaatIni;
        const iniSaatIni = idx === indeksSaatIni;
        const terakhir = idx === TAHAP.length - 1;
        const Ikon = tahap.ikon;

        return (
          <li key={tahap.kunci} className="flex gap-3">
            <div className="flex flex-col items-center">
              <span
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2 transition-colors duration-cepat ${
                  tercapai ? "border-daun bg-daun text-kertas" : "border-kabut bg-kertas text-tanah/35"
                } ${iniSaatIni ? "ring-2 ring-daun/25 ring-offset-2 ring-offset-kertas" : ""}`}
              >
                <Ikon aria-hidden className="h-4 w-4" strokeWidth={2.5} />
              </span>
              {!terakhir && (
                <span className={`w-0.5 flex-1 ${tercapai ? "bg-daun" : "bg-kabut"}`} style={{ minHeight: 28 }} />
              )}
            </div>
            <div className="pb-7 pt-1.5">
              <p
                className={`text-base ${iniSaatIni ? "font-bold text-tanah" : tercapai ? "font-medium text-tanah" : "text-tanah/50"}`}
              >
                {tahap.label}
              </p>
              <p className="angka text-keterangan text-tanah/60">{waktu ? formatWaktu(waktu) : "—"}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
