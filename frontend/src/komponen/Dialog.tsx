/** Dialog modal generik — bottom-sheet di layar sempit, kartu tengah di layar lebar.
 *  Dipakai untuk formulir "Ikut kirim", dialog dua pilihan luapan kapasitas (§5.5),
 *  dan konfirmasi "Tutup slot". Tanpa animasi masuk/keluar (aturan keras: hanya dua
 *  animasi di seluruh aplikasi, keduanya di layar Detail Slot — bukan ini). */

import { type ReactNode, useEffect } from "react";
import { createPortal } from "react-dom";

interface DialogProps {
  terbuka: boolean;
  onTutup: () => void;
  judul: string;
  children: ReactNode;
}

export default function Dialog({ terbuka, onTutup, judul, children }: DialogProps) {
  useEffect(() => {
    if (!terbuka) return;
    function tanganiTombol(e: KeyboardEvent) {
      if (e.key === "Escape") onTutup();
    }
    document.addEventListener("keydown", tanganiTombol);
    return () => document.removeEventListener("keydown", tanganiTombol);
  }, [terbuka, onTutup]);

  if (!terbuka) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-tanah/50 sm:items-center sm:p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onTutup();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="judul-dialog"
        className="flex max-h-[90vh] w-full max-w-md flex-col gap-4 overflow-y-auto rounded-t-2xl border-2 border-kabut bg-kertas p-5 sm:rounded-2xl"
      >
        <div className="flex items-center justify-between gap-3">
          <h2 id="judul-dialog" className="text-xl font-bold text-tanah">
            {judul}
          </h2>
          <button
            type="button"
            onClick={onTutup}
            aria-label="Tutup"
            className="flex min-h-sentuh min-w-sentuh items-center justify-center rounded-md text-2xl leading-none text-tanah/60 focus-visible:outline-daun"
          >
            ×
          </button>
        </div>
        {children}
      </div>
    </div>,
    document.body,
  );
}
