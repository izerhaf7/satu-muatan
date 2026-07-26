/** Timeline vertikal Lacak (§9.6): Dipesan -> Dimuat -> Jalan -> Tiba, tahap saat ini disorot. */

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

const TAHAP: { kunci: keyof TimelineOut; label: string }[] = [
  { kunci: "dipesan", label: "Dipesan" },
  { kunci: "dimuat", label: "Dimuat" },
  { kunci: "berangkat", label: "Jalan" },
  { kunci: "tiba", label: "Tiba" },
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

        return (
          <li key={tahap.kunci} className="flex gap-3">
            <div className="flex flex-col items-center">
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 ${
                  tercapai ? "border-daun bg-daun" : "border-kabut bg-kertas"
                }`}
              />
              {!terakhir && <span className={`w-0.5 flex-1 ${tercapai ? "bg-daun" : "bg-kabut"}`} style={{ minHeight: 24 }} />}
            </div>
            <div className="pb-6">
              <p className={`text-base ${iniSaatIni ? "font-bold text-tanah" : tercapai ? "font-medium text-tanah" : "text-tanah/50"}`}>
                {tahap.label}
              </p>
              <p className="angka text-sm text-tanah/60">{waktu ? formatWaktu(waktu) : "—"}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
