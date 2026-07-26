/** Hook dampak bulanan — sumber "ringkasan bulan ini" Beranda Koperasi (§9.2, K6). */

import { useQuery } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type DampakBulananOut = components["schemas"]["DampakBulananOut"];

export function useDampakBulanan() {
  return useQuery({
    queryKey: ["dampak", "bulanan"],
    queryFn: () => api<DampakBulananOut[]>("/api/dampak/bulanan"),
  });
}
