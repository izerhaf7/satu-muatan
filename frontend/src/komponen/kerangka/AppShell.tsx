/** Kerangka aplikasi ber-autentikasi: ponsel = bar akun atas + konten + NavBawah;
 *  desktop (≥lg) = NavSamping di kiri + kolom konten tengah yang lebih lebar.
 *  Semua layar authed dirender lewat <Outlet/> di dalam kerangka ini —
 *  padding bawah seragam (temuan audit: pb acak 16/24/28). Perilaku ponsel
 *  tidak berubah; penyesuaian desktop murni kelas lg: tambahan. */

import { LogOut } from "lucide-react";
import { Outlet, useNavigate } from "react-router-dom";

import { useAuthStore } from "@/stores/authStore";

import NavBawah from "./NavBawah";
import NavSamping from "./NavSamping";
import { LABEL_PERAN } from "./navigasi";

export default function AppShell() {
  const pengguna = useAuthStore((s) => s.pengguna);
  const keluar = useAuthStore((s) => s.keluar);
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <NavSamping />

      <div className="flex min-h-screen flex-1 flex-col lg:min-w-0">
        <div className="bar-akun-atas flex items-center justify-between gap-3 px-5 pt-3 lg:hidden">
          <div className="flex items-center gap-2.5">
            <img src="/ikon-192.png" alt="" className="h-8 w-8 rounded-full" />
            <div className="leading-tight">
              <p className="text-keterangan font-bold text-tanah">{pengguna?.nama}</p>
              <p className="text-[11px] font-medium uppercase tracking-wide text-daun">
                {LABEL_PERAN[pengguna?.peran ?? ""] ?? ""}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => {
              keluar();
              navigate("/masuk");
            }}
            className="inline-flex min-h-sentuh items-center gap-1.5 rounded-lg px-3 text-keterangan font-semibold text-tanah/60 transition-colors duration-cepat hover:bg-tanah/5 hover:text-tanah"
          >
            <LogOut aria-hidden className="h-4 w-4" />
            Keluar
          </button>
        </div>

        <main className="flex flex-1 flex-col px-5 pb-28 pt-2 lg:px-8 lg:pb-12">
          <div className="mx-auto flex w-full max-w-md flex-col gap-6 lg:max-w-3xl xl:max-w-5xl">
            <Outlet />
          </div>
        </main>
      </div>

      <NavBawah />
    </div>
  );
}
