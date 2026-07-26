/** Kartu Harga Atap milik petani yang login (§9.4 butir 2, §5.5, aturan keras #3).
 *  Nilainya TIDAK PERNAH animasi — atap terkunci sejak gabung, itulah maknanya.
 *  Gembok kecil menandai ini secara visual (bukan emoji, spec §10). */

import AngkaHarga from "@/komponen/AngkaHarga";
import IkonGembok from "@/komponen/IkonGembok";
import { formatRupiah } from "@/utils/format";

interface KartuAtapSayaProps {
  atapPerKg: number;
  hematPerKg: number | null;
  volumeSayaKg: number;
}

export default function KartuAtapSaya({ atapPerKg, hematPerKg, volumeSayaKg }: KartuAtapSayaProps) {
  const totalHemat = hematPerKg !== null ? hematPerKg * volumeSayaKg : null;

  return (
    <section aria-label="Harga atap kamu" className="flex flex-col gap-2 rounded-lg border-2 border-kabut p-4">
      <div className="flex items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 text-base text-tanah/80">
          <IkonGembok className="text-tanah/60" />
          Harga atap kamu
        </span>
        <AngkaHarga nilai={atapPerKg} ukuran="kecil" satuan="/kg" />
      </div>
      {hematPerKg !== null && (
        <div className="flex items-center justify-between gap-2">
          <span className="text-base text-tanah/80">Kamu hemat</span>
          <div className="text-right">
            <AngkaHarga nilai={hematPerKg} ukuran="kecil" satuan="/kg" className="text-daun" />
            {totalHemat !== null && totalHemat > 0 && (
              <p className="angka text-sm text-daun/80">≈ {formatRupiah(totalHemat)}</p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
