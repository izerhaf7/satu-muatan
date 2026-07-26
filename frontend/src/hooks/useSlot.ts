/** Hook slot — daftar (Beranda §9.2), pratinjau & buat (Buat Slot §9.3). */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type SlotItemOut = components["schemas"]["SlotItemOut"];
type SlotDetailOut = components["schemas"]["SlotDetailOut"];
type SlotCreate = components["schemas"]["SlotCreate"];
type StatusSlot = components["schemas"]["StatusSlot"];
type PratinjauSlotRequest = components["schemas"]["PratinjauSlotRequest"];
type PratinjauSlotResponse = components["schemas"]["PratinjauSlotResponse"];

/** Ter-scope per peran oleh server (K6): KOPERASI -> miliknya, PETANI -> koperasinya,
 *  PENERIMA -> slot yang menuju dirinya. */
export function useDaftarSlot(status?: StatusSlot) {
  return useQuery({
    queryKey: ["slot", status ?? "semua"],
    queryFn: () => {
      const qs = status ? `?status=${status}` : "";
      return api<SlotItemOut[]>(`/api/slot${qs}`);
    },
  });
}

export function useBuatSlot() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: SlotCreate) =>
      api<SlotDetailOut>("/api/slot", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["slot"] });
    },
  });
}

/** Pratinjau §9.3: jarak rute + tabel harga/kg pada berbagai skenario volume. */
export function usePratinjauSlot() {
  return useMutation({
    mutationFn: (body: PratinjauSlotRequest) =>
      api<PratinjauSlotResponse>("/api/slot/pratinjau", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}
