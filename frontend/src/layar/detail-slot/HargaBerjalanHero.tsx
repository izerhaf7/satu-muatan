/** Harga Berjalan — objek tipografi utama layar Detail Slot (§9.4 butir 1, §10).
 *  Satu-satunya tempat animasi count-up dipasang (lihat AngkaCountUp). */

import AngkaCountUp from "@/komponen/AngkaCountUp";

interface HargaBerjalanHeroProps {
  hargaPerKg: number | null;
}

export default function HargaBerjalanHero({ hargaPerKg }: HargaBerjalanHeroProps) {
  return (
    <section aria-label="Harga berjalan" className="flex flex-col items-center gap-1 py-4 text-center">
      <p className="text-sm font-semibold uppercase tracking-wide text-tanah/60">Harga berjalan</p>
      <AngkaCountUp nilai={hargaPerKg} ukuran="besar" satuan="/kg" />
    </section>
  );
}
