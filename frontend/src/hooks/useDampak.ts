/** Hook dampak — sumber "ringkasan bulan ini" Beranda Koperasi (§9.2, K6) dan
 *  Dashboard Dampak (§9.10): 4 kartu ringkasan + grafik batang per bulan. */

import { useQuery } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type DampakBulananOut = components["schemas"]["DampakBulananOut"];
type DampakRingkasanOut = components["schemas"]["DampakRingkasanOut"];

export function useDampakBulanan() {
  return useQuery({
    queryKey: ["dampak", "bulanan"],
    queryFn: () => api<DampakBulananOut[]>("/api/dampak/bulanan"),
  });
}

/** 4 kartu Dashboard Dampak: truk-km, emisi, penghematan ongkos, susut dicegah. */
export function useDampakRingkasan() {
  return useQuery({
    queryKey: ["dampak", "ringkasan"],
    queryFn: () => api<DampakRingkasanOut>("/api/dampak/ringkasan"),
  });
}
