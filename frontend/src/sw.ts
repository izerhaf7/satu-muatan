/// <reference lib="webworker" />
/** Service worker PWA — offline SHELL saja (spec §3.1), tanpa caching data API. */

import { cleanupOutdatedCaches, precacheAndRoute } from "workbox-precaching";

declare let self: ServiceWorkerGlobalScope;

cleanupOutdatedCaches();
precacheAndRoute(self.__WB_MANIFEST);

// Peta (Google Maps) WAJIB network-only: precache di atas hanya berisi shell +
// woff2 (spec §3.1), dan request Maps JS / tile / geocoding lintas-origin tidak
// boleh di-serve dari cache — kunci & token harus selalu dari jaringan. Tanpa
// respondWith, workbox routing tidak menyentuh request ini; guard di bawah
// mengunci perilaku itu supaya tidak berubah kalau handler lain ditambahkan.
self.addEventListener("fetch", (event: FetchEvent) => {
  const url = new URL(event.request.url);
  if (url.hostname.endsWith("googleapis.com") || url.hostname.endsWith("gstatic.com")) {
    event.respondWith(fetch(event.request));
  }
});
