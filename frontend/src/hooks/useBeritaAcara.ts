/** Hook Berita Acara (§9.8) — agregat lot, foto muat & bongkar, rincian ongkos,
 *  selisih jaminan atap. Tanda tangan = garis kosong cetak (K4), tanpa capture digital. */

import { useQuery } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type BeritaAcaraOut = components["schemas"]["BeritaAcaraOut"];

export function useBeritaAcara(slotId: string | undefined) {
  return useQuery({
    queryKey: ["berita-acara", slotId],
    queryFn: () => api<BeritaAcaraOut>(`/api/slot/${slotId}/berita-acara`),
    enabled: Boolean(slotId),
  });
}
