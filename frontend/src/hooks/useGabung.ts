/** Hook "Ikut kirim" (§9.4 butir 5, §5.5 JAMINAN ATAP) — pratinjau gabung (peringatan
 *  dini luapan) + gabung sungguhan, termasuk penanganan 409 LUAPAN_KAPASITAS. */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api, ApiError, type components } from "@/api/client";

type GabungPratinjauRequest = components["schemas"]["GabungPratinjauRequest"];
type GabungPratinjauResponse = components["schemas"]["GabungPratinjauResponse"];
type GabungRequest = components["schemas"]["GabungRequest"];
type GabungResponse = components["schemas"]["GabungResponse"];
export type LuapanKapasitasOut = components["schemas"]["LuapanKapasitasOut"];

/** Peringatan dini sebelum submit: atap, harga berjalan baru, potensi luapan. */
export function usePratinjauGabung(slotId: string) {
  return useMutation({
    mutationFn: (body: GabungPratinjauRequest) =>
      api<GabungPratinjauResponse>(`/api/slot/${slotId}/gabung/pratinjau`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}

/** "Ikut kirim" sungguhan — mengunci harga_atap_per_kg petani (tidak pernah berubah).
 *  Bisa gagal dengan 409 LUAPAN_KAPASITAS kalau kondisi berubah sejak pratinjau
 *  (peserta lain gabung duluan) — pemanggil menangani lewat `isLuapanKapasitas`. */
export function useGabungSlot(slotId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: GabungRequest) =>
      api<GabungResponse>(`/api/slot/${slotId}/gabung`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["slot", "detail", slotId] });
      void queryClient.invalidateQueries({ queryKey: ["slot"] });
    },
  });
}

/** Type guard: error dari useGabungSlot berupa body 409 LuapanKapasitasOut (§5.5)? */
export function isLuapanKapasitas(error: unknown): error is ApiError & { body: LuapanKapasitasOut } {
  return error instanceof ApiError && error.status === 409;
}
