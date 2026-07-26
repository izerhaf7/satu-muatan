/** Hook layar Serah Terima (§9.7, peran Penerima) — daftar lot masuk, cari via kode QR,
 *  kirim keputusan (Terima / Terima dengan potongan / Tolak). */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type BuktiLotOut = components["schemas"]["BuktiLotOut"];
type SerahTerimaCreate = components["schemas"]["SerahTerimaCreate"];
type SerahTerimaOut = components["schemas"]["SerahTerimaOut"];

/** Jalur utama (§9.7): "pilih dari daftar" — lot menuju penerima login, belum diserahterimakan. */
export function useLotMasuk() {
  return useQuery({
    queryKey: ["lot", "masuk"],
    queryFn: () => api<BuktiLotOut[]>("/api/lot/masuk"),
  });
}

/** Jalur manual: input kode QR lot secara langsung. Dipicu tombol "Cari", bukan otomatis. */
export function useCariLotQr() {
  return useMutation({
    mutationFn: (kodeQr: string) => api<BuktiLotOut>(`/api/lot/qr/${encodeURIComponent(kodeQr)}`),
  });
}

export function useKirimSerahTerima() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ lotId, body }: { lotId: string; body: SerahTerimaCreate }) =>
      api<SerahTerimaOut>(`/api/lot/${lotId}/serah-terima`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["lot", "masuk"] });
    },
  });
}
