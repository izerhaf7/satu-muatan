/** Nav publik sticky — translucent, muncul di atas semua section landing. */

import { Link } from "react-router-dom";

import TombolTautan from "@/komponen/TombolTautan";

export default function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b border-kabut/60 bg-kertas/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-2.5">
        <Link to="/" className="flex items-center gap-2.5 rounded-lg py-1">
          <img src="/ikon-192.png" alt="" className="h-8 w-8 rounded-lg" />
          <span className="text-base font-bold text-tanah">Satu Muatan</span>
        </Link>
        <TombolTautan to="/masuk">Masuk</TombolTautan>
      </div>
    </header>
  );
}
