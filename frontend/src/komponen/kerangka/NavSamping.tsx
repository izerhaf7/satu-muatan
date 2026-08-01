/** Navigasi samping (desktop ≥lg) — sidebar tetap di kiri: logo, kartu akun,
 *  daftar nav vertikal per peran, tombol keluar di kaki. Item nav dibagi dengan
 *  NavBawah lewat navigasi.ts. Tersembunyi total di bawah lg (ponsel pakai
 *  NavBawah; perilaku ponsel tidak berubah). */

import { LogOut } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";

import { useAuthStore } from "@/stores/authStore";

import { LABEL_PERAN, NAV_PER_PERAN } from "./navigasi";

export default function NavSamping() {
  const pengguna = useAuthStore((s) => s.pengguna);
  const keluar = useAuthStore((s) => s.keluar);
  const navigate = useNavigate();
  const item = NAV_PER_PERAN[pengguna?.peran ?? ""] ?? [];
  if (item.length === 0) return null;

  return (
    <nav
      aria-label="Navigasi utama"
      className="hidden lg:flex lg:w-64 lg:shrink-0 lg:flex-col lg:sticky lg:top-0 lg:h-screen lg:border-r lg:border-kabut lg:bg-kertas"
    >
      <div className="flex items-center gap-3 px-5 pt-6 pb-5">
        <img src="/ikon-192.png" alt="Satu Muatan" className="h-10 w-10 rounded-full" />
        <p className="text-subjudul font-bold text-tanah">Satu Muatan</p>
      </div>

      <div className="mx-5 mb-4 rounded-xl border border-kabut/70 bg-tanah/5 px-4 py-3 leading-tight">
        <p className="text-keterangan font-bold text-tanah">{pengguna?.nama}</p>
        <p className="text-[11px] font-medium uppercase tracking-wide text-daun">
          {LABEL_PERAN[pengguna?.peran ?? ""] ?? ""}
        </p>
      </div>

      <div className="flex flex-col gap-1 px-3">
        {item.map(({ ke, label, ikon: Ikon }) => (
          <NavLink
            key={ke}
            to={ke}
            className={({ isActive }) =>
              `flex min-h-sentuh items-center gap-3 rounded-lg px-3 text-base font-semibold transition-colors duration-cepat ${
                isActive ? "bg-daun/10 text-daun" : "text-tanah/60 hover:bg-tanah/5 hover:text-tanah"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Ikon aria-hidden className="h-5 w-5" strokeWidth={isActive ? 2.5 : 2} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </div>

      <div className="mt-auto border-t border-kabut/70 px-3 py-3">
        <button
          type="button"
          onClick={() => {
            keluar();
            navigate("/masuk");
          }}
          className="flex min-h-sentuh w-full items-center gap-3 rounded-lg px-3 text-base font-semibold text-tanah/60 transition-colors duration-cepat hover:bg-tanah/5 hover:text-tanah"
        >
          <LogOut aria-hidden className="h-5 w-5" />
          Keluar
        </button>
      </div>
    </nav>
  );
}
