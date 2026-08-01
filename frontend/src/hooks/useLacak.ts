/** Hook layar Lacak (§9.6) — timeline pengiriman, peta, majukan simulasi (K5). */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type SlotDetailOut = components["schemas"]["SlotDetailOut"];
type PengirimanOut = components["schemas"]["PengirimanOut"];
type TelemetriOut = components["schemas"]["TelemetriOut"];

const INTERVAL_POLL_MS = 3000; // spec §3.1: polling 3 detik, bukan WebSocket.

/** Info slot (kode, titik kumpul, daftar tujuan) — konteks header + titik peta. */
export function useSlotUntukLacak(slotId: string | undefined) {
  return useQuery({
    queryKey: ["slot", slotId, "ringkas-lacak"],
    queryFn: () => api<SlotDetailOut>(`/api/slot/${slotId}`),
    enabled: Boolean(slotId),
  });
}

/** Timeline + estimasi tiba + jejak posisi. Poll 3 detik selama belum TIBA. */
export function usePengirimanSlot(slotId: string | undefined) {
  return useQuery({
    queryKey: ["slot", slotId, "pengiriman"],
    queryFn: () => api<PengirimanOut>(`/api/slot/${slotId}/pengiriman`),
    enabled: Boolean(slotId),
    refetchInterval: (query) => (query.state.data?.timeline.tiba ? false : INTERVAL_POLL_MS),
  });
}

/** Telemetri suhu/kelembapan (spec v2 §5) — SIMULASI berlabel. Poll 3 detik
 *  selama belum TIBA (sampel bertambah per interval). */
export function useTelemetriSlot(slotId: string | undefined, sudahTiba: boolean) {
  return useQuery({
    queryKey: ["slot", slotId, "telemetri"],
    queryFn: () => api<TelemetriOut>(`/api/lacak/${slotId}/telemetri`),
    enabled: Boolean(slotId),
    refetchInterval: sudahTiba ? false : INTERVAL_POLL_MS,
  });
}

export function useMajukanPengiriman(slotId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (pengirimanId: string) =>
      api<PengirimanOut>(`/api/pengiriman/${pengirimanId}/majukan`, { method: "POST" }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["slot", slotId, "pengiriman"] });
      void queryClient.invalidateQueries({ queryKey: ["slot", slotId, "telemetri"] });
    },
  });
}
