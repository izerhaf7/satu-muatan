/** Kartu ringkas satu permintaan — daftar Permintaan (§9.7 alur Penerima & varian Koperasi). */

import type { components } from "@/api/client";
import { formatAngka, formatTanggal } from "@/utils/format";

import BadgePermintaan from "./BadgePermintaan";

type PermintaanOut = components["schemas"]["PermintaanOut"];

interface KartuPermintaanProps {
  permintaan: PermintaanOut;
  /** Tampilkan nama penerima (berguna untuk varian Koperasi yang melihat semua permintaan terbuka). */
  tampilkanPenerima?: boolean;
}

export default function KartuPermintaan({ permintaan, tampilkanPenerima = false }: KartuPermintaanProps) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border-2 border-kabut p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-base font-semibold text-tanah">{permintaan.nama_komoditas}</p>
          {tampilkanPenerima && <p className="text-sm text-tanah/60">{permintaan.nama_penerima}</p>}
        </div>
        <BadgePermintaan status={permintaan.status} />
      </div>

      <p className="angka text-lg font-bold text-tanah">
        {formatAngka(permintaan.volume_terpenuhi_kg)} / {formatAngka(permintaan.volume_kg)} kg
      </p>

      <p className="text-sm text-tanah/70">Dibutuhkan {formatTanggal(permintaan.tanggal_dibutuhkan)}</p>
    </div>
  );
}
