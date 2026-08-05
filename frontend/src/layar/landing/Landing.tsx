/** Landing publik v2 (impor desain Claude Design) — permukaan pemasaran di `/`,
 *  di luar cakupan batas animasi §10 aplikasi (K12 butir 4): reveal-on-scroll +
 *  animasi "perjalanan" scroll-driven diizinkan di sini, semua tetap tunduk
 *  prefers-reduced-motion. Beranda aplikasi ada di `/beranda`.
 *
 *  Palet & tipografi landing SENGAJA terpisah dari token aplikasi (lihat landing.css)
 *  — jangan pindahkan warna di sini ke tailwind.config.js / global.css. */

import "./landing.css";

import Atribusi from "./komponen/Atribusi";
import CaraKerja from "./komponen/CaraKerja";
import CtaPenutup from "./komponen/CtaPenutup";
import Faq from "./komponen/Faq";
import Hero from "./komponen/Hero";
import Masalah from "./komponen/Masalah";
import Nav from "./komponen/Nav";
import Perjalanan from "./komponen/Perjalanan";

export default function Landing() {
  return (
    <div className="lp-root flex min-h-screen flex-col">
      <Nav />
      <main className="flex-1">
        <Hero />
        <Masalah />
        <CaraKerja />
        <Perjalanan />
        <Atribusi />
        <Faq />
        <CtaPenutup />
      </main>
    </div>
  );
}
