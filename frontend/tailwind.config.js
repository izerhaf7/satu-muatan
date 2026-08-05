/** Palet 5 warna — spec §10. JANGAN menambah warna; nuansa lewat modifier
 *  opasitas (/5 /10 /20 /40 /60 /80) sebagai sistem tone resmi (K12).
 *  Direvisi mengikuti palet landing (navy+hijau) — nama token tetap sama
 *  supaya seluruh kelas `text-tanah`/`bg-daun`/dst di app tidak perlu diubah,
 *  hanya nilai hex-nya. tanah-liat sengaja TIDAK ikut palet landing (landing
 *  tidak punya warna bahaya/tolak) — dipertahankan merah terpisah demi
 *  kejelasan status TOLAK/error. */
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    colors: {
      transparent: "transparent",
      current: "currentColor",
      tanah: "#0F2D4A", // teks utama, latar gelap (Secondary landing)
      kertas: "#F5F6F8", // latar utama (Neutral Gray landing)
      daun: "#16A34A", // aksi utama, status baik (Primary landing)
      "tanah-liat": "#DC2626", // peringatan, penolakan — tidak ada di palet landing, dipertahankan agar TOLAK/error tetap jelas
      kabut: "#DDE3EA", // garis, pemisah, nonaktif (border landing)
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
        lembut: "0 1px 2px 0 rgba(15, 45, 74, 0.08)",
        sedang: "0 2px 8px -2px rgba(15, 45, 74, 0.12)",
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
