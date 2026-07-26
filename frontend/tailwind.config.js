/** Palet 5 warna — spec §10. JANGAN menambah warna. */
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
      // Angka & display: monospace teknis, tabular-nums wajib (lihat global.css)
      angka: ["'JetBrains Mono'", "'Courier New'", "monospace"],
      sans: ["system-ui", "'Segoe UI'", "sans-serif"],
    },
    extend: {
      fontSize: {
        base: "1rem", // body minimum 16 px (spec §10)
      },
      minHeight: {
        sentuh: "48px", // target sentuh minimum (spec §10)
      },
      minWidth: {
        sentuh: "48px",
      },
    },
  },
  plugins: [],
};
