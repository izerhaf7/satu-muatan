/** Hook perjalanan lengkap satu resi (K14, peran Penerima).
 *
 *  Otorisasinya RESI, bukan alamat: layar Lacak biasa memakai
 *  `pastikan_bisa_lihat_slot`, yang untuk penerima masih mencocokkan
 *  `penerima_id` dengan tujuan muatan — syarat yang tidak lagi terpenuhi sejak
 *  tujuan dibebaskan (K13). Endpoint ini menggantikannya. */

import { useQuery } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type PerjalananResiOut = components["schemas"]["PerjalananResiOut"];

const INTERVAL_POLL_MS = 3000; // spec §3.1: polling 3 detik, bukan WebSocket.

export function usePerjalananResi(kodeResi: string | null) {
  return useQuery({
    queryKey: ["perjalanan-resi", kodeResi],
    queryFn: () => api<PerjalananResiOut>(`/api/lacak/resi/${encodeURIComponent(kodeResi!)}`),
    enabled: Boolean(kodeResi),
    refetchInterval: (query) => (query.state.data?.pengiriman.timeline.tiba ? false : INTERVAL_POLL_MS),
  });
}
