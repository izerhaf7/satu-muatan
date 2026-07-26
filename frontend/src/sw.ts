/// <reference lib="webworker" />
/** Service worker PWA — offline SHELL saja (spec §3.1), tanpa caching data API. */

import { cleanupOutdatedCaches, precacheAndRoute } from "workbox-precaching";

declare let self: ServiceWorkerGlobalScope;

cleanupOutdatedCaches();
precacheAndRoute(self.__WB_MANIFEST);
