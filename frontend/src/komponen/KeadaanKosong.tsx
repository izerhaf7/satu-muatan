/** Keadaan kosong — wajib mengajak bertindak, bukan sekadar "Tidak ada data" (spec §10).
 *  Aksi opsional: `ke` (navigasi rute) atau `onAksi` (callback), dipakai salah satu.
 *  Ikon default PackageOpen bila `ikon` tak diisi pemanggil. */

import type { ReactNode } from "react";
import { PackageOpen } from "lucide-react";

import Tombol from "./Tombol";
import TombolTautan from "./TombolTautan";

interface KeadaanKosongProps {
  pesan: string;
  teksAksi?: string;
  ke?: string;
  onAksi?: () => void;
  ikon?: ReactNode;
}

export default function KeadaanKosong({ pesan, teksAksi, ke, onAksi, ikon }: KeadaanKosongProps) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-xl border-2 border-dashed border-kabut px-6 py-10 text-center">
      {ikon ?? <PackageOpen aria-hidden className="h-10 w-10 text-tanah/30" />}
      <p className="text-base text-tanah/80">{pesan}</p>
      {teksAksi && ke && (
        <TombolTautan to={ke} varian="aksi">
          {teksAksi} →
        </TombolTautan>
      )}
      {teksAksi && onAksi && !ke && (
        <Tombol type="button" varian="aksi" onClick={onAksi}>
          {teksAksi} →
        </Tombol>
      )}
    </div>
  );
}
