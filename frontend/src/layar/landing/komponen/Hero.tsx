/** Section hero Landing — teks kiri / truk 3D kanan (stack di mobile).
 *  HeroTiga (three.js) di-lazy-load lewat React.lazy supaya `three` +
 *  `@react-three/fiber` jadi chunk terpisah, tidak ikut bundle awal (verifikasi
 *  di `npm run build`). Suspense fallback = PosterTruk (statis) selagi chunk itu
 *  diunduh, jadi tidak ada layar kosong.
 *
 *  Truk 3D HANYA dipasang kalau: (1) bukan prefers-reduced-motion, DAN (2) kanvas
 *  browser benar-benar punya konteks WebGL. Selain itu, PosterTruk tampil permanen
 *  sebagai pengganti — bukan cuma fallback sementara. */

import { Suspense, lazy, useEffect, useRef, useState } from "react";

import { kelasDasarTombol, kelasVarianTombol } from "@/komponen/Tombol";
import TombolTautan from "@/komponen/TombolTautan";

import PosterTruk from "./PosterTruk";

const HeroTiga = lazy(() => import("./HeroTiga"));

function dukunganWebGL(): boolean {
  if (typeof document === "undefined") return false;
  try {
    const kanvas = document.createElement("canvas");
    return !!(kanvas.getContext("webgl2") || kanvas.getContext("webgl") || kanvas.getContext("experimental-webgl"));
  } catch {
    return false;
  }
}

export default function Hero() {
  const wadahRef = useRef<HTMLDivElement>(null);
  const [pakai3d, setPakai3d] = useState(false);
  const [terlihat, setTerlihat] = useState(true);

  // Deteksi kemampuan sekali saat mount — tidak reaktif terhadap perubahan setelahnya
  // (kalau pengguna mengganti pengaturan OS di tengah sesi, refresh cukup adil).
  useEffect(() => {
    const gerakanDikurangi = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true;
    setPakai3d(!gerakanDikurangi && dukunganWebGL());
  }, []);

  // IntersectionObserver: matikan loop invalidate begitu hero discroll lewat,
  // nyalakan lagi kalau discroll balik ke atas.
  useEffect(() => {
    if (!pakai3d) return;
    const elemen = wadahRef.current;
    if (!elemen) return;
    const observer = new IntersectionObserver(([entri]) => setTerlihat(entri.isIntersecting), { threshold: 0.05 });
    observer.observe(elemen);
    return () => observer.disconnect();
  }, [pakai3d]);

  return (
    <section className="mx-auto grid min-h-[88vh] max-w-6xl grid-cols-1 items-center gap-10 px-5 py-14 lg:grid-cols-2 lg:gap-12 lg:py-0">
      <div className="flex flex-col items-center gap-5 text-center lg:items-start lg:text-left">
        <p className="text-keterangan font-bold uppercase tracking-wide text-daun">
          Titik kumpul · Kirim bersama
        </p>
        <h1 className="text-display text-tanah">
          Satu muatan penuh.
          <br />
          <span className="text-daun">Ongkos turun sampai 75%.</span>
        </h1>
        <p className="max-w-md text-base text-tanah/70">
          Titik kumpul menggabungkan panen beberapa petani jadi satu pengiriman. Begitu Anda ikut, harga
          atap langsung terkunci — tidak pernah naik lagi walau slotnya makin penuh.
        </p>
        <div className="mt-2 flex flex-col gap-3 sm:flex-row">
          <TombolTautan to="/masuk" varian="aksi">
            Masuk
          </TombolTautan>
          <a href="#cara-kerja" className={`${kelasDasarTombol} ${kelasVarianTombol.sekunder}`}>
            Lihat cara kerja
          </a>
        </div>
      </div>

      <div ref={wadahRef} className="relative mx-auto h-[320px] w-full max-w-[420px] lg:h-[460px] lg:max-w-none">
        {pakai3d ? (
          <Suspense fallback={<PosterTruk className="h-full w-full" />}>
            <HeroTiga aktif={terlihat} wadahRef={wadahRef} />
          </Suspense>
        ) : (
          <PosterTruk className="h-full w-full" />
        )}
      </div>
    </section>
  );
}
