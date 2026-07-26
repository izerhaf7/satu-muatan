/** Hook daftar permintaan (§9.3 Buat Slot — "Penuhi permintaan dapur").
 *  Ter-scope per peran server-side (K6): KOPERASI melihat semua yang TERBUKA. */

import { useQuery } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type PermintaanOut = components["schemas"]["PermintaanOut"];

export function useDaftarPermintaan() {
  return useQuery({
    queryKey: ["permintaan"],
    queryFn: () => api<PermintaanOut[]>("/api/permintaan"),
  });
}
