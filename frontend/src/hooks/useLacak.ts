/** Hook layar Lacak (§9.6) — timeline pengiriman, peta, majukan simulasi (K5). */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type SlotDetailOut = components["schemas"]["SlotDetailOut"];
type PengirimanOut = components["schemas"]["PengirimanOut"];

const INTERVAL_POLL_MS = 3000; // spec §3.1: polling 3 detik, bukan WebSocket.

/** Info slot (kode, koperasi/gudang, daftar tujuan) — konteks header + titik peta. */
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

export function useMajukanPengiriman(slotId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (pengirimanId: string) =>
      api<PengirimanOut>(`/api/pengiriman/${pengirimanId}/majukan`, { method: "POST" }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["slot", slotId, "pengiriman"] });
    },
  });
}
