/** Scroll-reveal untuk Landing publik — landing DIKECUALIKAN dari batas "dua animasi"
 *  aplikasi (K12 butir 4), jadi hook ini boleh dipakai bebas di tiap section.
 *
 *  IntersectionObserver sekali-tampil: begitu elemen masuk viewport, `terlihat` jadi
 *  true dan tetap true (animasi kemunculan satu arah, bukan kedip masuk-keluar saat
 *  scroll naik-turun). Di bawah prefers-reduced-motion, observer tidak pernah dipasang
 *  — `terlihat` langsung true sejak render pertama, konten statis tampil apa adanya. */

import { useEffect, useRef, useState } from "react";

function gerakanDikurangi(): boolean {
  return typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true;
}

interface OpsiTampilSaatScroll {
  /** Porsi elemen yang harus terlihat sebelum dianggap "masuk viewport" (0–1). */
  ambang?: number;
  /** Geser titik pemicu, mis. "-10% 0px" supaya trigger sedikit sebelum masuk layar penuh. */
  rootMargin?: string;
}

export function useTampilSaatScroll<T extends HTMLElement = HTMLDivElement>(opsi: OpsiTampilSaatScroll = {}) {
  const { ambang = 0.2, rootMargin = "0px 0px -10% 0px" } = opsi;
  const ref = useRef<T | null>(null);
  const [terlihat, setTerlihat] = useState(() => gerakanDikurangi());

  useEffect(() => {
    if (gerakanDikurangi()) {
      setTerlihat(true);
      return;
    }
    const elemen = ref.current;
    if (!elemen) return;

    const observer = new IntersectionObserver(
      ([entri]) => {
        if (entri.isIntersecting) {
          setTerlihat(true);
          observer.disconnect();
        }
      },
      { threshold: ambang, rootMargin },
    );
    observer.observe(elemen);
    return () => observer.disconnect();
  }, [ambang, rootMargin]);

  return { ref, terlihat };
}

/** Kelas transisi seragam dipakai semua section: translate-y-4 opacity-0 → visible,
 *  ~500ms. Reduced-motion menutupi transisi lewat blok global di global.css, jadi
 *  kelas ini aman dipasang tanpa syarat tambahan. */
export function kelasScrollReveal(terlihat: boolean): string {
  return `transition-all duration-500 ease-out ${terlihat ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"}`;
}
