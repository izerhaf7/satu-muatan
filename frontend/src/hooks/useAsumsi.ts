/** Hook Panel Asumsi (§9.9, pembeda utama) — konfigurasi & tier kendaraan.
 *  Setelah PATCH berhasil, invalidasi SELURUH query (bukan cuma "konfigurasi"/"tier")
 *  supaya layar lain (Beranda, Detail Slot, Dashboard Dampak, dst.) ikut menghitung
 *  ulang dengan nilai baru — ini gerakan demo intinya: "ubah angka di sini, angka
 *  di layar lain ikut berubah". */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type KonfigurasiOut = components["schemas"]["KonfigurasiOut"];
type KonfigurasiPatch = components["schemas"]["KonfigurasiPatch"];
type TierKendaraanOut = components["schemas"]["TierKendaraanOut"];
type TierKendaraanPatch = components["schemas"]["TierKendaraanPatch"];

export function useDaftarKonfigurasi() {
  return useQuery({
    queryKey: ["konfigurasi"],
    queryFn: () => api<KonfigurasiOut[]>("/api/konfigurasi"),
  });
}

export function useUbahKonfigurasi() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ kunci, body }: { kunci: string; body: KonfigurasiPatch }) =>
      api<KonfigurasiOut>(`/api/konfigurasi/${kunci}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      // Sengaja tanpa queryKey — seluruh cache TanStack Query dianggap basi
      // karena konfigurasi ini dipakai mesin harga & dampak di banyak layar.
      void queryClient.invalidateQueries();
    },
  });
}

export function useDaftarTier() {
  return useQuery({
    queryKey: ["tier-kendaraan"],
    queryFn: () => api<TierKendaraanOut[]>("/api/tier-kendaraan"),
  });
}

export function useUbahTier() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: TierKendaraanPatch }) =>
      api<TierKendaraanOut>(`/api/tier-kendaraan/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries();
    },
  });
}
