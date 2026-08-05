/** Grafik garis suhu perjalanan vs waktu (spec v2 §5.4) — Recharts, garis ambang
 *  suhu acuan komoditas. Label WAJIB di bawah grafik: "Data simulasi — sensor
 *  fisik menyusul." (ukuran kecil, warna kabut) — menandai sendiri apa yang
 *  simulasi terlihat lebih percaya diri daripada berharap tidak ketahuan.
 *  Warna HANYA dari palet 5 warna (spec §10). Tanpa animasi. */

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { components } from "@/api/client";

type TelemetriOut = components["schemas"]["TelemetriOut"];

// Palet 5 warna (spec §10 / tailwind.config.js) — jangan tambah warna lain.
const WARNA_DAUN = "#16A34A";
const WARNA_TANAH_LIAT = "#DC2626";
const WARNA_KABUT = "#DDE3EA";
const WARNA_TANAH_60 = "rgba(15, 45, 74, 0.6)";

interface TitikSuhu {
  waktu: string;
  jam: string;
  suhu_c: number;
  kelembapan_persen: number;
}

function formatJamLokal(iso: string): string {
  return new Date(iso).toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });
}

interface TooltipSuhuProps {
  active?: boolean;
  payload?: { payload: TitikSuhu }[];
  label?: string;
}

function TooltipSuhu({ active, payload }: TooltipSuhuProps) {
  if (!active || !payload?.length) return null;
  const t = payload[0].payload;
  return (
    <div className="kartu-tonjol px-3 py-2 text-keterangan text-tanah">
      <p className="font-semibold">{formatJamLokal(t.waktu)}</p>
      <p className="angka text-base font-bold text-tanah-liat">{t.suhu_c.toFixed(1)} °C</p>
      <p className="angka text-tanah/60">Kelembapan {t.kelembapan_persen.toFixed(0)}%</p>
    </div>
  );
}

interface GrafikSuhuProps {
  telemetri: TelemetriOut;
}

export default function GrafikSuhu({ telemetri }: GrafikSuhuProps) {
  const data: TitikSuhu[] = telemetri.sampel.map((s) => ({
    waktu: s.waktu,
    jam: formatJamLokal(s.waktu),
    suhu_c: s.suhu_c,
    kelembapan_persen: s.kelembapan_persen,
  }));
  const suhuAcuan = telemetri.ringkasan?.suhu_acuan_c;

  return (
    <div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke={WARNA_KABUT} />
          <XAxis dataKey="jam" tick={{ fill: WARNA_TANAH_60, fontSize: 12 }} axisLine={{ stroke: WARNA_KABUT }} tickLine={false} />
          <YAxis
            domain={["dataMin - 2", "dataMax + 2"]}
            tickFormatter={(v: number) => `${Math.round(v)}°`}
            tick={{ fill: WARNA_TANAH_60, fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            width={40}
          />
          <Tooltip cursor={{ stroke: WARNA_KABUT }} content={<TooltipSuhu />} />
          {suhuAcuan !== undefined && (
            <ReferenceLine
              y={suhuAcuan}
              stroke={WARNA_DAUN}
              strokeDasharray="6 4"
              label={{ value: `Acuan ${suhuAcuan}°`, fill: WARNA_DAUN, fontSize: 11, position: "insideTopLeft" }}
            />
          )}
          <Line
            type="monotone"
            dataKey="suhu_c"
            stroke={WARNA_TANAH_LIAT}
            strokeWidth={2.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
      {/* Label WAJIB (spec v2 §5.4) — jangan dihilangkan. */}
      <p className="mt-2 text-center text-keterangan text-kabut">Data simulasi — sensor fisik menyusul.</p>
    </div>
  );
}
