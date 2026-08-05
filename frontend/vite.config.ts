import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

import { mockApiPlugin } from "./vite.mockApi";

// PWA: installable + offline shell saja (spec §3.1) — tanpa caching data API.
export default defineConfig({
  plugins: [
    react(),
    // MOCK DEV FASE 1 — mati secara default; aktif hanya lewat `VITE_MOCK=1 npm run dev`
    // (backend sungguhan masih 501 di worktree paralel saat Fase 1 ditulis).
    ...(process.env.VITE_MOCK === "1" ? [mockApiPlugin()] : []),
    VitePWA({
      // injectManifest (bukan generateSW): generateSW milik workbox menulis path
      // absolut tanpa escaping dan pecah pada path proyek yang mengandung tanda '
      strategies: "injectManifest",
      srcDir: "src",
      filename: "sw.ts",
      registerType: "autoUpdate",
      // woff2 wajib masuk precache — font self-host harus tersedia offline (K12)
      injectManifest: {
        globPatterns: ["**/*.{js,css,html,svg,png,ico,woff2}"],
        maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
      },
      manifest: {
        name: "Satu Muatan",
        short_name: "Satu Muatan",
        description: "Konsolidasi muatan & bukti mutu rantai pasok hortikultura",
        lang: "id",
        display: "standalone",
        background_color: "#F5F6F8",
        theme_color: "#16A34A",
        icons: [
          { src: "/ikon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/ikon-512.png", sizes: "512x512", type: "image/png" },
          { src: "/ikon-192-maskable.png", sizes: "192x192", type: "image/png", purpose: "maskable" },
          { src: "/ikon-512-maskable.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      "@kontrak": path.resolve(__dirname, "../kontrak"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // 127.0.0.1: hindari stall resolusi IPv6 "localhost" di Windows (lihat backend/app/config.py).
      // Port 8100: port 8000 dipakai layanan lain (uvicorn di WSL) pada mesin dev.
      "/api": { target: "http://127.0.0.1:8100", changeOrigin: true },
    },
  },
});
