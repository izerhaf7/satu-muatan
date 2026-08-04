/** Daftar penjemputan berurutan (K14) — layar kerja utama petugas.
 *
 *  Sebelumnya seluruh petani dianggap berangkat dari satu titik kumpul, jadi
 *  petugas tidak pernah diberi tahu ke mana harus menjemput. Padahal perannya
 *  justru itu: penghubung yang mendatangi kebun, memeriksa komoditas, lalu
 *  membawanya. Rute di sini sudah diurutkan sistem dari yang paling dekat.
 *
 *  Tombol peta membuka aplikasi peta perangkat — petugas di jalan butuh
 *  navigasi belokan-per-belokan, dan itu bukan sesuatu yang perlu kita tiru. */

import { MapPin, Navigation, Warehouse } from "lucide-react";

import type { components } from "@/api/client";
import { formatAngka } from "@/utils/format";

type RuteJemputOut = components["schemas"]["RuteJemputOut"];

interface DaftarJemputProps {
  jemput: RuteJemputOut[];
  namaTitikKumpul: string;
}

export default function DaftarJemput({ jemput, namaTitikKumpul }: DaftarJemputProps) {
  if (jemput.length === 0) return null;

  const totalKm = jemput.reduce((t, j) => t + j.jarak_segmen_km, 0);

  return (
    <section aria-label="Rute penjemputan" className="kartu-tonjol flex flex-col gap-3 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-0.5">
          <h2 className="text-subjudul text-tanah">Rute penjemputan</h2>
          <p className="text-keterangan text-tanah/55">
            Urut dari yang terdekat. Ambil semua sebelum mengantar.
          </p>
        </div>
        <p className="angka shrink-0 text-base font-semibold text-tanah">{formatAngka(totalKm)} km</p>
      </div>

      <ol className="flex flex-col">
        <li className="flex gap-3">
          <div className="flex flex-col items-center">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2 border-tanah/25 bg-kertas text-tanah/60">
              <Warehouse aria-hidden className="h-4 w-4" strokeWidth={2.25} />
            </span>
            <span className="w-0.5 flex-1 bg-kabut" style={{ minHeight: 24 }} />
          </div>
          <div className="pb-5 pt-1.5">
            <p className="text-base font-medium text-tanah">Berangkat dari {namaTitikKumpul}</p>
          </div>
        </li>

        {jemput.map((j, idx) => {
          const terakhir = idx === jemput.length - 1;
          return (
            <li key={j.partisipasi_id} className="flex gap-3">
              <div className="flex flex-col items-center">
                <span className="angka flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-2 border-daun bg-daun text-base font-bold text-kertas">
                  {j.urutan}
                </span>
                {!terakhir && <span className="w-0.5 flex-1 bg-daun" style={{ minHeight: 24 }} />}
              </div>

              <div className={`flex min-w-0 flex-1 flex-col gap-1.5 pt-1.5 ${terakhir ? "" : "pb-5"}`}>
                <div className="flex items-start justify-between gap-2">
                  <p className="text-base font-semibold text-tanah">{j.nama_petani}</p>
                  <p className="angka shrink-0 text-keterangan text-tanah/60">
                    {formatAngka(j.jarak_segmen_km)} km
                  </p>
                </div>
                <p className="flex items-start gap-1.5 text-keterangan text-tanah/70">
                  <MapPin aria-hidden className="mt-0.5 h-3.5 w-3.5 shrink-0 text-tanah/45" />
                  {j.alamat}
                </p>
                <a
                  href={`https://www.google.com/maps/dir/?api=1&destination=${j.lat},${j.lng}`}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex min-h-sentuh w-fit items-center gap-1.5 rounded-lg border-2 border-kabut px-3 text-keterangan font-semibold text-tanah/70 transition-colors duration-cepat hover:border-daun hover:text-daun"
                >
                  <Navigation aria-hidden className="h-3.5 w-3.5" />
                  Buka arah jalan
                </a>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
