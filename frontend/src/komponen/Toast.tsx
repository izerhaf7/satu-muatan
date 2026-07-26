/** Toast ringan (aria-live) untuk umpan balik mutasi — sukses/galat singkat.
 *  Tanpa animasi masuk-keluar di aplikasi (batas animasi spec §10 / K12). */

import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";
import { CheckCircle2, AlertCircle } from "lucide-react";

interface Toast {
  id: number;
  pesan: string;
  jenis: "sukses" | "galat";
}

const ToastContext = createContext<(pesan: string, jenis?: Toast["jenis"]) => void>(() => {});

export function useToast() {
  return useContext(ToastContext);
}

export function PenyediaToast({ children }: { children: ReactNode }) {
  const [daftar, setDaftar] = useState<Toast[]>([]);
  const idBerikut = useRef(1);

  const tampilkan = useCallback((pesan: string, jenis: Toast["jenis"] = "sukses") => {
    const id = idBerikut.current++;
    setDaftar((d) => [...d.slice(-2), { id, pesan, jenis }]);
    setTimeout(() => setDaftar((d) => d.filter((t) => t.id !== id)), 3500);
  }, []);

  return (
    <ToastContext.Provider value={tampilkan}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed inset-x-0 bottom-20 z-50 flex flex-col items-center gap-2 px-5"
      >
        {daftar.map((t) => (
          <div
            key={t.id}
            className={`flex max-w-md items-center gap-2.5 rounded-xl px-4 py-3 text-keterangan font-medium text-kertas shadow-sedang ${
              t.jenis === "sukses" ? "bg-daun" : "bg-tanah-liat"
            }`}
          >
            {t.jenis === "sukses" ? (
              <CheckCircle2 aria-hidden className="h-4 w-4 shrink-0" />
            ) : (
              <AlertCircle aria-hidden className="h-4 w-4 shrink-0" />
            )}
            {t.pesan}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
