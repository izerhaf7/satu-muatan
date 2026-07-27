/** Panel Harga Atap milik petani yang login (§9.4 butir 2, §5.5, aturan keras #3).
 *  Nilainya TIDAK PERNAH animasi — atap terkunci sejak gabung, itulah maknanya.
 *  Chip gembok kecil menandai ini secara visual (bukan emoji, spec §10). Dipakai
 *  HANYA menempel langsung di bawah HargaBerjalanHero (pemanggil membungkus
 *  keduanya jadi satu kartu, §9.4 mockup) — makanya tanpa sudut/bayangan sendiri. */

import IkonGembok from "@/komponen/IkonGembok";
import AngkaHarga from "@/komponen/AngkaHarga";
import { formatRupiah } from "@/utils/format";

interface KartuAtapSayaProps {
  atapPerKg: number;
  hematPerKg: number | null;
  volumeSayaKg: number;
}

export default function KartuAtapSaya({ atapPerKg, hematPerKg, volumeSayaKg }: KartuAtapSayaProps) {
  const totalHemat = hematPerKg !== null ? hematPerKg * volumeSayaKg : null;

  return (
    <section aria-label="Harga atap kamu" className="flex flex-col gap-3 border-t border-kabut/60 bg-kertas p-4">
      <div className="flex items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 text-base text-tanah/80">
          Harga atap kamu
          <span className="inline-flex items-center gap-1 rounded-full bg-tanah/5 px-2 py-0.5 text-keterangan font-semibold text-tanah/60">
            <IkonGembok className="text-tanah/50" />
            Terkunci
          </span>
        </span>
        <AngkaHarga nilai={atapPerKg} ukuran="kecil" satuan="/kg" />
      </div>

      {hematPerKg !== null && (
        <div className="flex items-center justify-between gap-3 rounded-lg bg-daun/10 px-3 py-2.5">
          <span className="text-base font-medium text-tanah">Kamu hemat</span>
          <div className="text-right">
            <p className="angka text-lg font-bold text-daun">
              {formatRupiah(hematPerKg)}
              <span className="ml-1 text-base font-normal text-daun/70">/kg</span>
            </p>
            {totalHemat !== null && totalHemat > 0 && (
              <p className="angka text-sm text-daun/80">≈ {formatRupiah(totalHemat)}</p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
