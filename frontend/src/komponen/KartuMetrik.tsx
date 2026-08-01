/** Kartu metrik besar dengan sumber & rumus (§9.10 Dashboard Dampak).
 *  `nilai=null` WAJIB tampil "—" + "Belum ada data" — jangan pernah nol yang
 *  terlihat seperti hasil hitung (spec §7, aturan kejujuran). Kartu berbasis
 *  koefisien ASUMSI ditandai visual berbeda (garis putus-putus) dari TERVERIFIKASI. */

import type { components } from "@/api/client";
import { formatAngka } from "@/utils/format";

import AngkaHarga from "./AngkaHarga";
import BadgeSumber from "./BadgeSumber";
import Tooltip from "./Tooltip";

type StatusSumber = components["schemas"]["StatusSumber"];

export type TampilanKartuMetrik = "angka" | "rupiah";

interface KartuMetrikProps {
  label: string;
  nilai: number | null;
  satuan: string;
  statusSumber: StatusSumber;
  rumus: string;
  catatanSumber?: string | null;
  /** "rupiah" pakai AngkaHarga (Rp di depan); "angka" pakai satuan di belakang angka. */
  tampilan?: TampilanKartuMetrik;
  /** Sub-teks kecil di bawah angka (kartu semboyan, spec v2 §7.1). */
  subTeks?: string | null;
}

export default function KartuMetrik({
  label,
  nilai,
  satuan,
  statusSumber,
  rumus,
  catatanSumber,
  tampilan = "angka",
  subTeks,
}: KartuMetrikProps) {
  const asumsi = statusSumber === "ASUMSI";

  return (
    <div
      className={`flex min-w-0 flex-col gap-3 rounded-lg border-2 p-4 ${
        asumsi ? "border-dashed border-kabut" : "border-kabut"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-tanah/70">{label}</p>
        <Tooltip label={`Lihat rumus ${label}`}>
          <p className="mb-1 font-semibold text-tanah">Rumus</p>
          <p className="angka text-tanah/90">{rumus}</p>
          {catatanSumber && <p className="mt-2 text-tanah/70">Sumber: {catatanSumber}</p>}
        </Tooltip>
      </div>

      {nilai === null ? (
        <div className="flex flex-col gap-0.5">
          <p className="angka text-3xl font-bold text-tanah/30">—</p>
          <p className="text-sm text-tanah/50">Belum ada data</p>
        </div>
      ) : tampilan === "rupiah" ? (
        <AngkaHarga nilai={nilai} ukuran="besar" />
      ) : (
        <p className="angka break-words text-3xl font-bold text-tanah">
          {formatAngka(nilai)}
          <span className="ml-1 text-base font-normal text-tanah/70">{satuan}</span>
        </p>
      )}

      {nilai !== null && subTeks && <p className="text-keterangan text-tanah/60">{subTeks}</p>}

      <BadgeSumber status={statusSumber} />
    </div>
  );
}
