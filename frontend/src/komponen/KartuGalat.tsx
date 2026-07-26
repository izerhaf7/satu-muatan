/** Satu komponen galat untuk seluruh aplikasi — menggantikan blok yang
 *  sebelumnya disalin-tempel 12×. Selalu menawarkan aksi pemulihan. */

import { CloudOff } from "lucide-react";

import Tombol from "./Tombol";

interface KartuGalatProps {
  pesan?: string;
  onCobaLagi?: () => void;
}

export default function KartuGalat({ pesan = "Gagal memuat data.", onCobaLagi }: KartuGalatProps) {
  return (
    <div role="alert" className="kartu-datar flex flex-col items-start gap-3 border-tanah-liat/40 p-4">
      <div className="flex items-center gap-2.5">
        <CloudOff aria-hidden className="h-5 w-5 shrink-0 text-tanah-liat" />
        <p className="text-base text-tanah">{pesan}</p>
      </div>
      {onCobaLagi && (
        <Tombol varian="sekunder" onClick={onCobaLagi} className="min-h-11 px-4 text-keterangan">
          Coba lagi
        </Tombol>
      )}
    </div>
  );
}
