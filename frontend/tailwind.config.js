/** Palet 5 warna — spec §10. JANGAN menambah warna; nuansa lewat modifier
 *  opasitas (/5 /10 /20 /40 /60 /80) sebagai sistem tone resmi (K12). */
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    colors: {
      transparent: "transparent",
      current: "currentColor",
      tanah: "#2B2119", // teks utama, latar gelap
      kertas: "#FAF7F2", // latar utama
      daun: "#2F6B3A", // aksi utama, status baik
      "tanah-liat": "#C1502E", // peringatan, penolakan
      kabut: "#D8D2C7", // garis, pemisah, nonaktif
    },
    fontFamily: {
      // Angka & display teknis: JetBrains Mono (dimuat via @fontsource di global.css)
      angka: ["'JetBrains Mono'", "'Courier New'", "monospace"],
      // UI: Plus Jakarta Sans (variable) — grotesque modern rancangan Indonesia
      sans: ["'Plus Jakarta Sans Variable'", "system-ui", "'Segoe UI'", "sans-serif"],
    },
    extend: {
      fontSize: {
        base: ["1rem", { lineHeight: "1.5" }], // body minimum 16 px (spec §10)
        keterangan: ["0.8125rem", { lineHeight: "1.4" }], // 13px meta/caption
        subjudul: ["1.25rem", { lineHeight: "1.3", fontWeight: "600" }], // 20px
        judul: ["1.75rem", { lineHeight: "1.15", fontWeight: "700", letterSpacing: "-0.01em" }], // 28px
        display: ["2.75rem", { lineHeight: "1.05", fontWeight: "800", letterSpacing: "-0.02em" }], // 44px
      },
      boxShadow: {
        // Elevasi halus — BUKAN kartu melayang berbayang tebal (larangan §10)
        lembut: "0 1px 2px 0 rgba(43, 33, 25, 0.08)",
        sedang: "0 2px 8px -2px rgba(43, 33, 25, 0.12)",
      },
      minHeight: {
        sentuh: "48px", // target sentuh minimum (spec §10)
      },
      minWidth: {
        sentuh: "48px",
      },
      transitionDuration: {
        // Micro-feedback interaksi (K12) — bukan animasi dekoratif
        cepat: "150ms",
      },
    },
  },
  plugins: [],
};
