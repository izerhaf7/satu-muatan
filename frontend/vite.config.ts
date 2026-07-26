import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vite";
import { VitePWA } from "vite-plugin-pwa";

// PWA: installable + offline shell saja (spec §3.1) — tanpa caching data API.
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      // injectManifest (bukan generateSW): generateSW milik workbox menulis path
      // absolut tanpa escaping dan pecah pada path proyek yang mengandung tanda '
      strategies: "injectManifest",
      srcDir: "src",
      filename: "sw.ts",
      registerType: "autoUpdate",
      manifest: {
        name: "Satu Muatan",
        short_name: "Satu Muatan",
        description: "Konsolidasi muatan & bukti mutu rantai pasok hortikultura",
        lang: "id",
        display: "standalone",
        background_color: "#FAF7F2",
        theme_color: "#2F6B3A",
        icons: [],
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
      "/api": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
