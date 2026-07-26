/** Beranda Penerima (§9.2 varian) — pintu masuk ke Permintaan (§9.7, placeholder Fase 1). */

import { Link } from "react-router-dom";

export default function BerandaPenerima() {
  return (
    <main className="flex flex-1 flex-col gap-6 px-5 py-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-tanah">Beranda</h1>
        <p className="text-base text-tanah/70">Kelola permintaan komoditas Anda</p>
      </header>

      <Link
        to="/permintaan"
        className="flex min-h-sentuh items-center justify-center rounded-md bg-daun px-5 text-base font-semibold text-kertas"
      >
        Lihat permintaan
      </Link>
    </main>
  );
}
