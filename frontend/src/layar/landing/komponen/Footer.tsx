/** Footer publik — wordmark, kredit lomba, tautan Masuk. */

import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="border-t border-kabut/60 px-5 py-8">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-3 text-center sm:flex-row sm:justify-between sm:text-left">
        <div className="flex items-center gap-2.5">
          <img src="/ikon-192.png" alt="" className="h-7 w-7 rounded-lg" />
          <span className="text-base font-bold text-tanah">Satu Muatan</span>
        </div>
        <p className="text-keterangan text-tanah/60">Karya lomba IT Festival 2026 — Sekolah Vokasi IPB</p>
        <Link
          to="/masuk"
          className="text-keterangan font-semibold text-daun underline-offset-4 hover:underline"
        >
          Masuk
        </Link>
      </div>
    </footer>
  );
}
