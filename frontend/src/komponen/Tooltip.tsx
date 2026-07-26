/** Tooltip diketuk/diklik — BUKAN hover-only (wajib di HP, §9.10).
 *  Dipakai kartu Dashboard Dampak untuk menampilkan rumus + sumber angka,
 *  tapi generik: siapa pun boleh pakai untuk info tambahan ringkas.
 *  Tanpa animasi. Target sentuh tombol pemicu tetap 48 px meski ikonnya kecil. */

import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { Info } from "lucide-react";

interface TooltipProps {
  /** Label aksesibilitas tombol pemicu, mis. "Lihat rumus truk-km dihemat". */
  label: string;
  children: ReactNode;
}

export default function Tooltip({ label, children }: TooltipProps) {
  const [terbuka, setTerbuka] = useState(false);
  const bungkusRef = useRef<HTMLDivElement>(null);
  const idIsi = useId();

  useEffect(() => {
    if (!terbuka) return;

    function tutupKalauDiluar(e: MouseEvent) {
      if (bungkusRef.current && !bungkusRef.current.contains(e.target as Node)) setTerbuka(false);
    }
    function tutupKalauEscape(e: KeyboardEvent) {
      if (e.key === "Escape") setTerbuka(false);
    }

    document.addEventListener("click", tutupKalauDiluar);
    document.addEventListener("keydown", tutupKalauEscape);
    return () => {
      document.removeEventListener("click", tutupKalauDiluar);
      document.removeEventListener("keydown", tutupKalauEscape);
    };
  }, [terbuka]);

  return (
    <div ref={bungkusRef} className="relative inline-flex">
      <button
        type="button"
        aria-expanded={terbuka}
        aria-describedby={terbuka ? idIsi : undefined}
        aria-label={label}
        onClick={() => setTerbuka((v) => !v)}
        className={`flex min-h-sentuh min-w-sentuh items-center justify-center rounded-lg transition-colors duration-cepat hover:bg-tanah/5 active:bg-tanah/10 ${
          terbuka ? "text-daun" : "text-tanah/60"
        }`}
      >
        <Info aria-hidden className="h-5 w-5" strokeWidth={2.25} />
      </button>
      {terbuka && (
        <div id={idIsi} role="tooltip" className="kartu-tonjol absolute right-0 top-full z-20 mt-1 w-64 max-w-[80vw] p-3 text-keterangan text-tanah">
          {children}
        </div>
      )}
    </div>
  );
}
