/** Hook Detail Slot (§9.4) — layar utama demo. Polling 3 detik lewat `refetchInterval`
 *  (aturan keras/§12: polling, bukan WebSocket) supaya harga berjalan & daftar peserta
 *  ikut bergerak tanpa aksi pengguna. Juga menyediakan mutasi "Tutup slot" (koperasi). */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type SlotDetailOut = components["schemas"]["SlotDetailOut"];

export function useDetailSlot(slotId: string | undefined) {
  return useQuery({
    queryKey: ["slot", "detail", slotId],
    queryFn: () => api<SlotDetailOut>(`/api/slot/${slotId}`),
    enabled: Boolean(slotId),
    refetchInterval: 3000,
  });
}

/** Tutup slot (§5.4, peran Koperasi): tetapkan harga final + jaminan atap, kunci
 *  rencana armada, buat lot, pesan ke vendor. */
export function useTutupSlot(slotId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api<SlotDetailOut>(`/api/slot/${slotId}/tutup`, { method: "POST" }),
    onSuccess: (data) => {
      queryClient.setQueryData(["slot", "detail", slotId], data);
      void queryClient.invalidateQueries({ queryKey: ["slot"] });
    },
  });
}
