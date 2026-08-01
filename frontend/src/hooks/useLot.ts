/** Hook layar Muat (§9.5, peran Petugas) — daftar lot slot, timbang per lot, selesai muat. */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type SlotDetailOut = components["schemas"]["SlotDetailOut"];
type LotOut = components["schemas"]["LotOut"];
type MuatPatchRequest = components["schemas"]["MuatPatchRequest"];

/** Info ringkas slot (kode, status) untuk header layar Muat. */
export function useSlotUntukMuat(slotId: string | undefined) {
  return useQuery({
    queryKey: ["slot", slotId, "ringkas-muat"],
    queryFn: () => api<SlotDetailOut>(`/api/slot/${slotId}`),
    enabled: Boolean(slotId),
  });
}

export function useDaftarLotSlot(slotId: string | undefined) {
  return useQuery({
    queryKey: ["slot", slotId, "lot"],
    queryFn: () => api<LotOut[]>(`/api/slot/${slotId}/lot`),
    enabled: Boolean(slotId),
  });
}

export function useMuatLot(slotId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ lotId, body }: { lotId: string; body: MuatPatchRequest }) =>
      api<LotOut>(`/api/lot/${lotId}/muat`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["slot", slotId, "lot"] });
    },
  });
}

export function useSelesaiMuat(slotId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api<LotOut[]>(`/api/slot/${slotId}/selesai-muat`, { method: "POST" }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["slot", slotId, "lot"] });
      void queryClient.invalidateQueries({ queryKey: ["slot", slotId, "ringkas-muat"] });
    },
  });
}
