/** Landing publik (Fase 2.6) — permukaan pemasaran di `/`, di luar cakupan batas
 *  animasi §10 (K12 butir 4): hero three.js lazy-chunk + scroll-reveal diizinkan,
 *  semua tetap tunduk prefers-reduced-motion. Beranda aplikasi ada di `/beranda`. */

import AngkaBand from "./komponen/AngkaBand";
import CaraKerja from "./komponen/CaraKerja";
import CtaPenutup from "./komponen/CtaPenutup";
import FiturUnggulan from "./komponen/FiturUnggulan";
import Footer from "./komponen/Footer";
import Hero from "./komponen/Hero";
import Nav from "./komponen/Nav";

export default function Landing() {
  return (
    <div className="flex min-h-screen flex-col">
      <Nav />
      <main className="flex-1">
        <Hero />
        <AngkaBand />
        <CaraKerja />
        <FiturUnggulan />
        <CtaPenutup />
      </main>
      <Footer />
    </div>
  );
}
