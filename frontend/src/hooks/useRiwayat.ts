/** Hook Riwayat (§2.5, layar utama Petani) — daftar ikut kirim + kembalian milik
 *  petani yang sedang login. */

import { useQuery } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type PartisipasiRiwayatOut = components["schemas"]["PartisipasiRiwayatOut"];

export function useRiwayatSaya() {
  return useQuery({
    queryKey: ["partisipasi", "saya"],
    queryFn: () => api<PartisipasiRiwayatOut[]>("/api/partisipasi/saya"),
  });
}
