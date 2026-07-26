/** Header layar seragam: tombol kembali (satu gaya untuk semua layar),
 *  judul + subjudul, dan slot aksi kanan. Sticky dengan latar buram halus. */

import { ArrowLeft } from "lucide-react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";

interface HeaderLayarProps {
  judul: string;
  subjudul?: ReactNode;
  /** Rute tujuan tombol kembali; tanpa nilai = tidak ada tombol kembali. */
  kembaliKe?: string;
  aksi?: ReactNode;
}

export default function HeaderLayar({ judul, subjudul, kembaliKe, aksi }: HeaderLayarProps) {
  const navigate = useNavigate();
  return (
    <header className="sticky top-0 z-30 -mx-5 flex items-center gap-2 border-b border-kabut/70 bg-kertas/90 px-5 py-3 backdrop-blur-sm">
      {kembaliKe && (
        <button
          type="button"
          aria-label="Kembali"
          onClick={() => navigate(kembaliKe)}
          className="-ml-2 inline-flex min-h-sentuh min-w-sentuh items-center justify-center rounded-lg text-tanah transition-colors duration-cepat hover:bg-tanah/5"
        >
          <ArrowLeft aria-hidden className="h-6 w-6" />
        </button>
      )}
      <div className="min-w-0 flex-1">
        <h1 className="truncate text-subjudul font-bold text-tanah">{judul}</h1>
        {subjudul && <div className="truncate text-keterangan text-tanah/60">{subjudul}</div>}
      </div>
      {aksi}
    </header>
  );
}
