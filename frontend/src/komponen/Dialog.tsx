/** Dialog modal generik — bottom-sheet di layar sempit, kartu tengah di layar lebar.
 *  Dipakai untuk formulir "Ikut kirim", dialog dua pilihan luapan kapasitas (§5.5),
 *  dan konfirmasi "Tutup slot". Tanpa animasi masuk/keluar (aturan keras: hanya dua
 *  animasi di seluruh aplikasi, keduanya di layar Detail Slot — bukan ini).
 *
 *  Aksesibilitas modal (K12): jebakan fokus (Tab tidak boleh lolos ke belakang layar),
 *  fokus awal ke elemen pertama saat terbuka, fokus dikembalikan ke pemicu saat tutup,
 *  dan scroll body dikunci selama dialog terbuka. */

import { type ReactNode, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

interface DialogProps {
  terbuka: boolean;
  onTutup: () => void;
  judul: string;
  children: ReactNode;
}

const SELEKTOR_FOKUS =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export default function Dialog({ terbuka, onTutup, judul, children }: DialogProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const elemenSebelumFokus = useRef<HTMLElement | null>(null);

  // Escape untuk menutup + jebakan fokus (Tab/Shift+Tab berputar di dalam panel).
  useEffect(() => {
    if (!terbuka) return;

    function tanganiTombol(e: KeyboardEvent) {
      if (e.key === "Escape") {
        onTutup();
        return;
      }
      if (e.key !== "Tab" || !panelRef.current) return;

      const fokusabel = Array.from(panelRef.current.querySelectorAll<HTMLElement>(SELEKTOR_FOKUS));
      if (fokusabel.length === 0) return;

      const pertama = fokusabel[0];
      const terakhir = fokusabel[fokusabel.length - 1];

      if (e.shiftKey && document.activeElement === pertama) {
        e.preventDefault();
        terakhir.focus();
      } else if (!e.shiftKey && document.activeElement === terakhir) {
        e.preventDefault();
        pertama.focus();
      }
    }

    document.addEventListener("keydown", tanganiTombol);
    return () => document.removeEventListener("keydown", tanganiTombol);
  }, [terbuka, onTutup]);

  // Kunci scroll body + pindahkan fokus awal ke panel; kembalikan keduanya saat tutup.
  useEffect(() => {
    if (!terbuka) return;

    elemenSebelumFokus.current = document.activeElement as HTMLElement | null;
    const overflowSebelumnya = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    const fokusabel = panelRef.current?.querySelectorAll<HTMLElement>(SELEKTOR_FOKUS);
    (fokusabel && fokusabel[0] ? fokusabel[0] : panelRef.current)?.focus();

    return () => {
      document.body.style.overflow = overflowSebelumnya;
      elemenSebelumFokus.current?.focus();
    };
  }, [terbuka]);

  if (!terbuka) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-tanah/50 sm:items-center sm:p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onTutup();
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="judul-dialog"
        tabIndex={-1}
        className="flex max-h-[90vh] w-full max-w-md flex-col gap-4 overflow-y-auto rounded-t-2xl border border-kabut bg-kertas p-5 shadow-sedang sm:rounded-2xl"
      >
        <div className="flex items-center justify-between gap-3">
          <h2 id="judul-dialog" className="text-xl font-bold text-tanah">
            {judul}
          </h2>
          <button
            type="button"
            onClick={onTutup}
            aria-label="Tutup"
            className="flex min-h-sentuh min-w-sentuh items-center justify-center rounded-lg text-tanah/60 transition-colors duration-cepat hover:bg-tanah/5 hover:text-tanah active:bg-tanah/10"
          >
            <X aria-hidden className="h-5 w-5" strokeWidth={2.25} />
          </button>
        </div>
        {children}
      </div>
    </div>,
    document.body,
  );
}
