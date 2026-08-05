/** Hero — headline word-reveal (CSS murni, animasi sekali muncul di load), dua
 *  CTA (utama → /masuk, sekunder → #cara-kerja), dan TrukIlustrasi 2D beranimasi.
 *  Truk memudar halus saat discroll lewat (mengikuti window.scrollY, bukan
 *  progres section #perjalanan — dua efek independen demi kesederhanaan). */

import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";

import { useTampilSaatScroll } from "../useTampilSaatScroll";
import TrukIlustrasi from "./TrukIlustrasi";

function gerakanDikurangi(): boolean {
  return typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true;
}

export default function Hero() {
  const truckWrapRef = useRef<HTMLDivElement>(null);
  const leadReveal = useTampilSaatScroll<HTMLParagraphElement>();
  const ctaReveal = useTampilSaatScroll<HTMLDivElement>();
  const noteReveal = useTampilSaatScroll<HTMLParagraphElement>();

  useEffect(() => {
    if (gerakanDikurangi()) return;
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const wrap = truckWrapRef.current;
        if (!wrap) return;
        const vh = window.innerHeight || 1;
        const f = Math.max(0, Math.min(1, window.scrollY / (vh * 0.7)));
        wrap.style.opacity = String(1 - f);
        wrap.style.transform = `translateY(${(f * 48).toFixed(1)}px)`;
      });
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <section id="atas" className="lp-hero" aria-labelledby="hero-judul">
      <div className="lp-hero__grid">
        <div>
          <h1 id="hero-judul" className="lp-hero__title">
            <span className="lp-hero__word">
              <span>Turunkan ongkos angkut,</span>
            </span>
            <span className="lp-hero__word">
              <span style={{ animationDelay: "90ms" }}>kurangi emisi, amankan muatan —</span>
            </span>
            <span className="lp-hero__word lp-hero__word--accent">
              <span className="lp-hero__accent" style={{ animationDelay: "180ms" }}>
                dari kebun sampai meja makan.
                <svg
                  aria-hidden="true"
                  className="lp-hero__underline"
                  viewBox="0 0 300 24"
                  preserveAspectRatio="none"
                >
                  <path
                    d="M4 15 C 62 5, 118 20, 176 10 C 226 2, 268 12, 296 7"
                    fill="none"
                    stroke="#16A34A"
                    strokeWidth={7}
                    strokeLinecap="round"
                  />
                </svg>
              </span>
            </span>
          </h1>

          <p ref={leadReveal.ref} className={`lp-hero__lead lp-reveal ${leadReveal.terlihat ? "is-visible" : ""}`}>
            <strong style={{ fontWeight: 700, opacity: 1 }}>Satu Muatan</strong> menggabungkan kiriman beberapa
            petani yang searah menjadi satu truk penuh. Satu perjalanan menggantikan empat — ongkosnya dibagi,
            emisinya berkurang, dan kondisi muatannya tercatat sepanjang jalan.
          </p>

          <div ref={ctaReveal.ref} className={`lp-hero__ctas lp-reveal ${ctaReveal.terlihat ? "is-visible" : ""}`}>
            <Link to="/masuk" className="lp-btn lp-btn--isi">
              Hitung ongkos kirimanku
            </Link>
            <a href="#cara-kerja" className="lp-btn lp-btn--garis">
              Lihat cara kerjanya
            </a>
          </div>
          <p ref={noteReveal.ref} className={`lp-hero__note lp-reveal ${noteReveal.terlihat ? "is-visible" : ""}`}>
            Gratis dicoba. Pembelimu tetap pembelimu.
          </p>
        </div>

        <div ref={truckWrapRef} className="lp-hero__truck-wrap">
          <div className="lp-hero__ground" aria-hidden="true" />
          <div className="lp-hero__ground-accent" aria-hidden="true" />
          <TrukIlustrasi />
          <div className="lp-hero__stats">
            <span>CDD · 2.000 KG</span>
            <span>TERISI 1.200 KG</span>
            <span className="lp-hero__stats--aksen angka">RP426/KG</span>
          </div>
        </div>
      </div>
    </section>
  );
}
