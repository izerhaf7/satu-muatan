/** Navigasi bawah per peran (ponsel <lg) — memperbaiki 4 rute yatim temuan audit.
 *  PETUGAS: Beranda · Dampak · Asumsi | PETANI: Beranda · Riwayat |
 *  PENERIMA: Permintaan · Serah Terima. Target sentuh 48px, ikon + label.
 *  Item nav dibagi dengan NavSamping (desktop) lewat navigasi.ts. */

import { NavLink } from "react-router-dom";

import { useAuthStore } from "@/stores/authStore";

import { NAV_PER_PERAN } from "./navigasi";

export default function NavBawah() {
  const pengguna = useAuthStore((s) => s.pengguna);
  const item = NAV_PER_PERAN[pengguna?.peran ?? ""] ?? [];
  if (item.length === 0) return null;

  return (
    <nav
      aria-label="Navigasi utama"
      className="fixed inset-x-0 bottom-0 z-30 border-t border-kabut bg-kertas/95 pb-[env(safe-area-inset-bottom)] backdrop-blur-sm lg:hidden"
    >
      <div className="mx-auto flex max-w-md items-stretch justify-around">
        {item.map(({ ke, label, ikon: Ikon }) => (
          <NavLink
            key={ke}
            to={ke}
            className={({ isActive }) =>
              `flex min-h-sentuh flex-1 flex-col items-center justify-center gap-0.5 py-2 text-[11px] font-semibold transition-colors duration-cepat ${
                isActive ? "text-daun" : "text-tanah/50 hover:text-tanah/80"
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
    </nav>
  );
}
