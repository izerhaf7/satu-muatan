/** Grafik batang penghematan ongkos per bulan (§9.10) — Recharts, satu seri jadi
 *  tanpa legenda (judul kartu sudah menamainya). Warna HANYA dari palet 5 warna
 *  (spec §10, sama dengan tailwind.config.js) — di-hardcode di sini karena SVG
 *  fill attribute Recharts tidak selalu resolve CSS custom property lintas browser.
 *  Tanpa animasi (aturan layar ini): `isAnimationActive={false}`. */

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { components } from "@/api/client";
import { formatAngka, formatBulan, formatRupiah } from "@/utils/format";

type DampakBulananOut = components["schemas"]["DampakBulananOut"];

// Palet 5 warna (spec §10 / tailwind.config.js) — jangan tambah warna lain.
const WARNA_DAUN = "#2F6B3A";
const WARNA_KABUT = "#D8D2C7";
const WARNA_TANAH_60 = "rgba(43, 33, 25, 0.6)"; // teks sumbu — tanah/60, bukan solid

function labelBulanSingkat(bulan: string): string {
  const [tahun, bulanKe] = bulan.split("-").map(Number);
  if (!tahun || !bulanKe) return bulan;
  return new Date(tahun, bulanKe - 1, 1).toLocaleDateString("id-ID", { month: "short" });
}

interface TooltipGrafikProps {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
}

function TooltipGrafik({ active, payload, label }: TooltipGrafikProps) {
  if (!active || !payload?.length || !label) return null;
  return (
    <div className="kartu-tonjol px-3 py-2 text-keterangan text-tanah">
      <p className="font-semibold">{formatBulan(label)}</p>
      <p className="angka text-base font-bold text-daun">{formatRupiah(payload[0].value)}</p>
    </div>
  );
}

interface GrafikBulananProps {
  data: DampakBulananOut[];
}

export default function GrafikBulanan({ data }: GrafikBulananProps) {
  return (
    <div className="kartu-tonjol p-4">
      <p className="mb-3 text-base font-semibold text-tanah">Penghematan ongkos per bulan</p>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }} barCategoryGap="30%">
          <CartesianGrid vertical={false} stroke={WARNA_KABUT} />
          <XAxis
            dataKey="bulan"
            tickFormatter={labelBulanSingkat}
            tick={{ fill: WARNA_TANAH_60, fontSize: 12 }}
            axisLine={{ stroke: WARNA_KABUT }}
            tickLine={false}
          />
          <YAxis
            tickFormatter={(nilai: number) => formatAngka(nilai)}
            tick={{ fill: WARNA_TANAH_60, fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            width={56}
          />
          <Tooltip cursor={{ fill: WARNA_KABUT, opacity: 0.4 }} content={<TooltipGrafik />} />
          <Bar
            dataKey="penghematan_rp"
            name="Penghematan"
            fill={WARNA_DAUN}
            radius={[4, 4, 0, 0]}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
