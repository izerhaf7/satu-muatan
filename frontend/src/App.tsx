/** Peta rute (react-router) — Fase 2.6:
 *  - `/` = Landing publik (authed → redirect /beranda)
 *  - Layar ber-autentikasi dibungkus AppShell (header akun + NavBawah)
 *  - Rute berat (peta Leaflet, grafik Recharts, berita acara) di-lazy-load
 *    supaya chunk masuk tidak menyeret dependensi yang belum dibutuhkan. */

import { Suspense, lazy } from "react";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";

import BatasGalat from "./komponen/BatasGalat";
import AppShell from "./komponen/kerangka/AppShell";
import RuteDenganPeran from "./komponen/kerangka/RuteDenganPeran";
import { SkeletonKartu } from "./komponen/Skeleton";
import Beranda from "./layar/Beranda";
import DetailSlot from "./layar/DetailSlot";
import KirimPanen from "./layar/KirimPanen";
import LacakResi from "./layar/LacakResi";
import Landing from "./layar/landing/Landing";
import Masuk from "./layar/Masuk";
import Muat from "./layar/Muat";
import Riwayat from "./layar/Riwayat";
import SerahTerima from "./layar/SerahTerima";
import { useAuthStore } from "./stores/authStore";

const Lacak = lazy(() => import("./layar/Lacak"));
const DashboardDampak = lazy(() => import("./layar/DashboardDampak"));
const BeritaAcara = lazy(() => import("./layar/BeritaAcara"));
const PanelAsumsi = lazy(() => import("./layar/PanelAsumsi"));

function SplashLogo() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-kertas">
      <img src="/ikon-192.png" alt="Satu Muatan" className="h-16 w-16" />
    </div>
  );
}

function PerluMasuk() {
  const token = useAuthStore((s) => s.token);
  return token ? <Outlet /> : <Navigate to="/masuk" replace />;
}

export default function App() {
  const token = useAuthStore((s) => s.token);
  const telahHidrasi = useAuthStore((s) => s.telahHidrasi);

  // Tunggu localStorage selesai dibaca dulu — cegah kedipan redirect saat refresh.
  if (!telahHidrasi) return <SplashLogo />;

  return (
    /* K14: boundary DI LUAR Suspense — supaya kegagalan memuat chunk lazy
       (mis. index.html lama dari service worker menunjuk hash yang sudah tidak
       ada) ikut tertangkap, bukan berakhir jadi layar putih. */
    <BatasGalat>
    <Suspense fallback={<div className="mx-auto max-w-md px-5 py-6 lg:max-w-3xl xl:max-w-5xl"><SkeletonKartu /></div>}>
      <Routes>
        <Route path="/" element={token ? <Navigate to="/beranda" replace /> : <Landing />} />
        <Route path="/masuk" element={token ? <Navigate to="/beranda" replace /> : <Masuk />} />

        <Route element={<PerluMasuk />}>
          <Route element={<AppShell />}>
            <Route path="/beranda" element={<Beranda />} />
            {/* K14: hanya petani yang mengirim panen — petugas adalah driver. */}
            <Route
              path="/kirim"
              element={
                <RuteDenganPeran peran={["PETANI"]}>
                  <KirimPanen />
                </RuteDenganPeran>
              }
            />
            {/* K13: rute /slot/baru DIHAPUS — tidak ada lagi "buka slot". */}
            <Route path="/slot/:id" element={<DetailSlot />} />
            <Route
              path="/slot/:id/muat"
              element={
                <RuteDenganPeran peran={["PETUGAS"]}>
                  <Muat />
                </RuteDenganPeran>
              }
            />
            <Route path="/slot/:id/lacak" element={<Lacak />} />
            <Route path="/slot/:id/berita-acara" element={<BeritaAcara />} />
            <Route
              path="/lacak-resi"
              element={
                <RuteDenganPeran peran={["PENERIMA"]}>
                  <LacakResi />
                </RuteDenganPeran>
              }
            />
            <Route
              path="/serah-terima"
              element={
                <RuteDenganPeran peran={["PENERIMA"]}>
                  <SerahTerima />
                </RuteDenganPeran>
              }
            />
            <Route
              path="/asumsi"
              element={
                <RuteDenganPeran peran={["PETUGAS"]}>
                  <PanelAsumsi />
                </RuteDenganPeran>
              }
            />
            <Route path="/dampak" element={<DashboardDampak />} />
            <Route
              path="/riwayat"
              element={
                <RuteDenganPeran peran={["PETANI"]}>
                  <Riwayat />
                </RuteDenganPeran>
              }
            />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to={token ? "/beranda" : "/"} replace />} />
      </Routes>
    </Suspense>
    </BatasGalat>
  );
}
