/** Kartu ringkas satu permintaan — daftar Permintaan (§9.7 alur Penerima & varian Petugas). */

import { CalendarClock } from "lucide-react";

import BarKapasitas from "@/komponen/BarKapasitas";
import type { components } from "@/api/client";
import { formatAngka, formatTanggal } from "@/utils/format";

import BadgePermintaan from "./BadgePermintaan";

type PermintaanOut = components["schemas"]["PermintaanOut"];

interface KartuPermintaanProps {
  permintaan: PermintaanOut;
  /** Tampilkan nama penerima (berguna untuk varian Petugas yang melihat semua permintaan terbuka). */
  tampilkanPenerima?: boolean;
}

export default function KartuPermintaan({ permintaan, tampilkanPenerima = false }: KartuPermintaanProps) {
  return (
    <div className="kartu-datar flex flex-col gap-3 p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-base font-semibold text-tanah">{permintaan.nama_komoditas}</p>
          {tampilkanPenerima && <p className="text-keterangan text-tanah/60">{permintaan.nama_penerima}</p>}
        </div>
        <BadgePermintaan status={permintaan.status} />
      </div>

      <div className="flex flex-col gap-1.5">
        <p className="angka text-lg font-bold text-tanah">
          {formatAngka(permintaan.volume_terpenuhi_kg)} / {formatAngka(permintaan.volume_kg)} kg
        </p>
        <BarKapasitas
          volumeKg={permintaan.volume_terpenuhi_kg}
          kapasitasKg={permintaan.volume_kg}
          className="[&_p]:hidden"
        />
      </div>

      <p className="flex items-center gap-1.5 text-keterangan text-tanah/70">
        <CalendarClock aria-hidden className="h-3.5 w-3.5 shrink-0" />
        Dibutuhkan {formatTanggal(permintaan.tanggal_dibutuhkan)}
      </p>
    </div>
  );
}
