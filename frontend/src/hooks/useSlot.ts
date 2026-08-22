/** Hook muatan — daftar untuk Beranda (§9.2).
 *
 *  K13: `useBuatSlot` & `usePratinjauSlot` DIHAPUS. Muatan tidak pernah dibuka
 *  manusia — ia lahir sendiri dari kiriman petani (lihat `useKiriman.ts`).
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type SlotItemOut = components["schemas"]["SlotItemOut"];
type StatusSlot = components["schemas"]["StatusSlot"];

/** Ter-scope per peran oleh server (K13): PETUGAS -> muatan yang ditugaskan
 *  padanya, PETANI -> muatan tempat dia ikut, PENERIMA -> muatan menuju dirinya. */
export function useDaftarSlot(status?: StatusSlot) {
  return useQuery({
    queryKey: ["slot", status ?? "semua"],
    queryFn: () => {
      const qs = status ? `?status=${status}` : "";
      return api<SlotItemOut[]>(`/api/slot${qs}`);
    },
  });
}

/** K14: PAPAN TUGAS — muatan yang belum punya driver dan bisa diambil petugas
 *  ini. Menggantikan penugasan otomatis K13, yang membuat satu petugas aktif
 *  menyerap seluruh muatan di sistem tanpa bisa diubah. */
export function useSlotTersedia(aktif = true) {
  return useQuery({
    queryKey: ["slot", "tersedia"],
    queryFn: () => api<SlotItemOut[]>("/api/slot/tersedia"),
    enabled: aktif,
  });
}

export function useTerimaTugas() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (slotId: string) => api<SlotItemOut>(`/api/slot/${slotId}/terima`, { method: "POST" }),
    onSuccess: () => {
      // Tugas berpindah dari papan ke daftar miliknya — keduanya jadi basi.
      void queryClient.invalidateQueries({ queryKey: ["slot"] });
    },
  });
}
