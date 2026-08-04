/** Bingkai aman untuk peta Leaflet — K14.
 *
 *  react-leaflet 4 membuat instance peta di dalam ref-callback yang dijaga
 *  "sudah pernah dibuat?", tapi menghancurkannya di cleanup effect. Di bawah
 *  React 18 `StrictMode` (dipasang di main.tsx) siklus mount disimulasikan dua
 *  kali: cleanup menghancurkan peta, lalu remount TIDAK membuatnya ulang karena
 *  penjaga tadi masih menyala. Anak-anaknya (TileLayer/Marker/Polyline) lalu
 *  memanggil peta yang sudah mati — yang berakhir sebagai throw saat render,
 *  dan tanpa error boundary itu tampil sebagai layar putih.
 *
 *  Bingkai ini menunda mount satu efek DAN memberi `key` yang berganti tiap
 *  siklus, sehingga setiap kali React memasang ulang, peta lahir di elemen DOM
 *  yang benar-benar baru. */

import { useEffect, useRef, useState, type ReactNode } from "react";

interface BingkaiPetaProps {
  children: ReactNode;
  /** Tinggi peta dalam piksel — 360px tetap jadi acuan (CLAUDE.md aturan #6). */
  tinggi?: number;
  className?: string;
}

export default function BingkaiPeta({ children, tinggi = 280, className = "" }: BingkaiPetaProps) {
  const siklus = useRef(0);
  const [siap, setSiap] = useState(false);

  useEffect(() => {
    siklus.current += 1;
    setSiap(true);
    return () => setSiap(false);
  }, []);

  return (
    <div className={`kartu-tonjol overflow-hidden rounded-xl ${className}`} style={{ height: tinggi }}>
      {siap ? <div key={siklus.current} style={{ height: "100%", width: "100%" }}>{children}</div> : null}
    </div>
  );
}
