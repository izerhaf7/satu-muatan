/** Keadaan kosong — wajib mengajak bertindak, bukan sekadar "Tidak ada data" (spec §10).
 *  Aksi opsional: `ke` (navigasi rute) atau `onAksi` (callback), dipakai salah satu. */

import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface KeadaanKosongProps {
  pesan: string;
  teksAksi?: string;
  ke?: string;
  onAksi?: () => void;
  ikon?: ReactNode;
}

const kelasTombolAksi =
  "inline-flex min-h-sentuh items-center justify-center gap-2 rounded-md bg-daun px-5 text-base font-semibold text-kertas";

export default function KeadaanKosong({ pesan, teksAksi, ke, onAksi, ikon }: KeadaanKosongProps) {
  return (
    <div className="flex flex-col items-center gap-4 rounded-lg border-2 border-dashed border-kabut px-6 py-10 text-center">
      {ikon}
      <p className="text-base text-tanah/80">{pesan}</p>
      {teksAksi && ke && (
        <Link to={ke} className={kelasTombolAksi}>
          {teksAksi} →
        </Link>
      )}
      {teksAksi && onAksi && !ke && (
        <button type="button" onClick={onAksi} className={kelasTombolAksi}>
          {teksAksi} →
        </button>
      )}
    </div>
  );
}
