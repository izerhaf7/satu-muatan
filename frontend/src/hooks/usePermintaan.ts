/** Hook layar Permintaan (§9.7 alur Penerima) — daftar & buat permintaan komoditas.
 *  Ter-scope per peran oleh server (K6): PENERIMA -> miliknya, KOPERASI -> semua yang terbuka. */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type PermintaanOut = components["schemas"]["PermintaanOut"];
type PermintaanCreate = components["schemas"]["PermintaanCreate"];

export function useDaftarPermintaan() {
  return useQuery({
    queryKey: ["permintaan"],
    queryFn: () => api<PermintaanOut[]>("/api/permintaan"),
  });
}

export function useBuatPermintaan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: PermintaanCreate) =>
      api<PermintaanOut>("/api/permintaan", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["permintaan"] });
    },
  });
}
