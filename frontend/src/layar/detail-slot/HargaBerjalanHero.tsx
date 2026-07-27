/** Harga Berjalan — objek tipografi utama layar Detail Slot (§9.4 butir 1, §10).
 *  Kartu-hero (bg-daun/text-kertas): angka raksasa duduk di atas panel terang supaya
 *  AngkaCountUp bisa dipakai TANPA sentuhan sama sekali (perilaku persis sama —
 *  termasuk warna tanah/daun bawaannya, termasuk panah turun ↓ — tetap terbaca jelas
 *  di panel terang, bukan berjuang melawan warna hijau latar hero). Saat KartuAtapSaya
 *  ikut ditampilkan (petani sudah gabung), pemanggil membungkus kartu ini + KartuAtapSaya
 *  supaya menyatu jadi satu kartu (§9.4 mockup: satu kotak, garis pemisah di tengah). */

import AngkaCountUp from "@/komponen/AngkaCountUp";

interface HargaBerjalanHeroProps {
  hargaPerKg: number | null;
}

export default function HargaBerjalanHero({ hargaPerKg }: HargaBerjalanHeroProps) {
  return (
    <section aria-label="Harga berjalan" className="flex flex-col items-center gap-4 bg-daun px-5 py-7 text-center text-kertas">
      <p className="text-keterangan font-bold uppercase tracking-[0.14em] text-kertas/75">Harga berjalan</p>
      <div className="inline-flex items-baseline gap-1.5 rounded-2xl bg-kertas px-6 py-3.5">
        <AngkaCountUp nilai={hargaPerKg} ukuran="besar" className="text-display" />
        {hargaPerKg !== null && <span className="text-lg font-medium text-tanah/60">/kg</span>}
      </div>
    </section>
  );
}
