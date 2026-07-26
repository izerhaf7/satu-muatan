/** Hook daftar penerima (tujuan pilihan Buat Slot §9.3). */

import { useQuery } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type PenerimaOut = components["schemas"]["PenerimaOut"];

export function useDaftarPenerima() {
  return useQuery({
    queryKey: ["penerima"],
    queryFn: () => api<PenerimaOut[]>("/api/penerima"),
  });
}
