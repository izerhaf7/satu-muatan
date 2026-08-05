/** #perjalanan — section paling kompleks: sticky-scroll (200vh mobile / 300vh
 *  desktop, lihat landing.css) yang menganimasikan TrukJalan menyusuri jalan
 *  sambil discroll, dengan 5 kartu titik informasi yang muncul berurutan.
 *
 *  Port dari setupJourney/togglePoint (script asli Component class) ke React:
 *  posisi truk/roda/kartu dimanipulasi LANGSUNG lewat ref DOM di dalam satu loop
 *  requestAnimationFrame (bukan setState per frame — soal performa), dibaca dari
 *  window.scrollY setiap frame tanpa scroll listener terpisah. Dibersihkan penuh
 *  di cleanup useEffect (cancelAnimationFrame) supaya tidak bocor antar mount
 *  (proyek ini pernah kena bug StrictMode double-invoke di react-leaflet).
 *
 *  Di bawah prefers-reduced-motion, loop ini TIDAK PERNAH dipasang — state akhir
 *  (truk & semua kartu titik tampil, progress penuh) langsung digambar sekali. */

import type { CSSProperties } from "react";
import { useEffect, useRef } from "react";

import TrukJalan from "./TrukJalan";

interface Titik {
  label: string;
  desc: string;
  angka: string;
  badge: string;
  badgeSimulasi?: boolean;
  side: "atas" | "bawah";
  leftPct: number;
  at: number;
}

const TITIK: Titik[] = [
  {
    label: "TITIK MUAT",
    desc: "Foto dan hasil timbang tiap lot direkam saat dimuat, jadi titik acuan mutu awal.",
    angka: "4 lot terekam",
    badge: "TERVERIFIKASI",
    side: "atas",
    leftPct: 12,
    at: 0.12,
  },
  {
    label: "SUHU MUATAN",
    desc: "Suhu dipantau sepanjang perjalanan dan dibandingkan dengan suhu acuan komoditas.",
    angka: "Maks 31,2 °C",
    badge: "SIMULASI",
    badgeSimulasi: true,
    side: "bawah",
    leftPct: 29,
    at: 0.26,
  },
  {
    label: "SISA UMUR SIMPAN",
    desc: "Dihitung dari suhu nyata sepanjang jalan — makin panas, makin cepat umur simpannya habis.",
    angka: "71% tersisa",
    badge: "TERVERIFIKASI",
    side: "bawah",
    leftPct: 46,
    at: 0.4,
  },
  {
    label: "WAKTU TEMPUH",
    desc: "Durasi perjalanan dibandingkan ambang wajar rute ini.",
    angka: "178 / 181 menit",
    badge: "TERVERIFIKASI",
    side: "atas",
    leftPct: 65,
    at: 0.54,
  },
  {
    label: "SERAH TERIMA",
    desc: "Pemindaian QR di tujuan mengunci waktu tiba dan membuka penilaian mutu.",
    angka: "QR terverifikasi",
    badge: "TERVERIFIKASI",
    side: "bawah",
    leftPct: 84,
    at: 0.68,
  },
];

const STOP = 0.82;
const JARAK_KM = 70.03;
const WAKTU_MENIT = 178;

function gerakanDikurangi(): boolean {
  return typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true;
}

const formatKm = new Intl.NumberFormat("id-ID", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export default function Perjalanan() {
  const stageRef = useRef<HTMLElement>(null);
  const headRef = useRef<HTMLDivElement>(null);
  const layer1Ref = useRef<HTMLDivElement>(null);
  const layer2Ref = useRef<HTMLDivElement>(null);
  const dashRef = useRef<HTMLDivElement>(null);
  const truckRef = useRef<HTMLDivElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const markerRef = useRef<HTMLDivElement>(null);
  const kmRef = useRef<HTMLSpanElement>(null);
  const menitRef = useRef<HTMLSpanElement>(null);
  const pointsRef = useRef<(HTMLDivElement | null)[]>([]);

  useEffect(() => {
    const stage = stageRef.current;
    if (!stage) return;

    const points = pointsRef.current.filter((el): el is HTMLDivElement => !!el);
    const onState = points.map(() => false);

    if (gerakanDikurangi()) {
      if (truckRef.current) truckRef.current.style.opacity = "1";
      points.forEach((el) => el.classList.add("is-on"));
      if (kmRef.current) kmRef.current.textContent = formatKm.format(JARAK_KM);
      if (menitRef.current) menitRef.current.textContent = String(WAKTU_MENIT);
      if (markerRef.current && trackRef.current) {
        markerRef.current.style.transform = `translateX(${trackRef.current.clientWidth - 9}px)`;
      }
      return;
    }

    const wheels = [...stage.querySelectorAll<SVGGElement>("[data-roda]")];
    const narrowQuery = window.matchMedia("(max-width: 639px)");

    let raf = 0;
    let lastY = window.scrollY;
    let vel = 0;
    let rot = 0;
    let dashOff = 0;

    const tick = () => {
      raf = requestAnimationFrame(tick);
      const y = window.scrollY;
      const dy = y - lastY;
      lastY = y;
      const vh = window.innerHeight || 1;

      const r = stage.getBoundingClientRect();
      if (r.bottom < 0 || r.top > vh) {
        vel = 0;
        return;
      }

      const t = Math.max(0, Math.min(1, -r.top / Math.max(1, r.height - vh)));
      const moving = t > 0.015 && t < STOP;
      vel = vel * 0.86 + (moving ? dy : 0) * 0.14;
      if (Math.abs(vel) < 0.02) vel = 0;

      rot += vel * 1.05;
      wheels.forEach((w) => {
        w.style.transform = `rotate(${rot.toFixed(2)}deg)`;
      });

      dashOff = (dashOff + Math.abs(vel) * 1.7) % 104;
      if (dashRef.current) dashRef.current.style.transform = `translateX(${(-dashOff).toFixed(1)}px)`;

      if (layer1Ref.current) layer1Ref.current.style.transform = `translateX(${(-t * 40).toFixed(1)}px)`;
      if (layer2Ref.current) layer2Ref.current.style.transform = `translateX(${(-t * 20).toFixed(1)}px)`;

      if (headRef.current) headRef.current.style.opacity = t > 0.1 ? "0" : "1";

      if (truckRef.current) {
        truckRef.current.style.opacity = String(Math.min(1, t / 0.05));
        const shake = Math.abs(vel) > 0.35 ? (Math.random() * 2 - 1) * 1.6 : 0;
        truckRef.current.style.transform = `translate(-50%, -76%) translateY(${shake.toFixed(2)}px)`;
      }

      const p = Math.min(1, t / STOP);
      if (kmRef.current) kmRef.current.textContent = formatKm.format(JARAK_KM * p);
      if (menitRef.current) menitRef.current.textContent = String(Math.round(WAKTU_MENIT * p));
      if (markerRef.current && trackRef.current) {
        const w = trackRef.current.clientWidth - 9;
        markerRef.current.style.transform = `translateX(${(p * w).toFixed(1)}px)`;
      }

      const narrow = narrowQuery.matches;
      points.forEach((el, i) => {
        const at = TITIK[i].at;
        const on = t >= at;
        if (on === onState[i]) return;
        onState[i] = on;
        el.classList.toggle("is-on", on);
        if (on && narrow) {
          points.forEach((other, j) => {
            if (j !== i && onState[j]) {
              onState[j] = false;
              other.classList.remove("is-on");
            }
          });
        }
      });
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <section
      id="perjalanan"
      ref={stageRef}
      className="lp-perjalanan"
      aria-labelledby="perjalanan-judul"
    >
      <div className="lp-perjalanan__sticky">
        <div ref={headRef} className="lp-perjalanan__head">
          <h2 id="perjalanan-judul" className="lp-perjalanan__head-eyebrow">
            Simulasi perjalanan · gudang Mekarjaya → SPPG Cibiru 3
          </h2>
          <p className="lp-perjalanan__head-judul">Ikuti satu muatan, dari titik muat sampai serah terima.</p>
        </div>

        <div ref={layer2Ref} className="lp-perjalanan__layer" aria-hidden="true" />
        <div ref={layer1Ref} className="lp-perjalanan__layer" aria-hidden="true" />

        <div className="lp-perjalanan__road">
          <div ref={dashRef} className="lp-perjalanan__road-dash" />
        </div>
        <div className="lp-perjalanan__road-edge" aria-hidden="true" />

        <div ref={truckRef} className="lp-perjalanan__truck">
          <TrukJalan />
        </div>

        {TITIK.map((titik, i) => (
          <div
            key={titik.label}
            ref={(el) => {
              pointsRef.current[i] = el;
            }}
            className={`lp-perjalanan__point lp-perjalanan__point--${titik.side}`}
            style={{ "--lp-point-left": `${titik.leftPct}%` } as CSSProperties}
          >
            <div className="lp-perjalanan__dot" />
            <div className="lp-perjalanan__conn" />
            <div className="lp-perjalanan__card">
              <p className="lp-perjalanan__card-label">{titik.label}</p>
              <p className="lp-perjalanan__card-desc">{titik.desc}</p>
              <p className="lp-perjalanan__card-angka angka">{titik.angka}</p>
              <span
                className={`lp-perjalanan__card-badge ${titik.badgeSimulasi ? "lp-perjalanan__card-badge--simulasi" : ""}`}
              >
                {titik.badge}
              </span>
            </div>
          </div>
        ))}

        <div className="lp-perjalanan__progress">
          <div className="lp-perjalanan__progress-row">
            <span className="angka">
              <span ref={kmRef}>0,00</span> km <span>/ 70,03</span>
            </span>
            <span className="angka">
              <span ref={menitRef}>0</span> menit <span>/ 178</span>
            </span>
          </div>
          <div ref={trackRef} className="lp-perjalanan__track">
            <div ref={markerRef} className="lp-perjalanan__marker" />
          </div>
        </div>
      </div>
    </section>
  );
}
