/** Hook kiriman (spec v2 §3.5) — pratinjau atap+potensi dan kirim panen. */

import { useMutation, useQuery } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type KirimanResponse = components["schemas"]["KirimanResponse"];
type KirimanPratinjauResponse = components["schemas"]["KirimanPratinjauResponse"];
type KirimanCreate = components["schemas"]["KirimanCreate"];

export interface ParamsPratinjau {
  volumeKg: number;
  lat: number;
  lng: number;
  tanggal: string; // ISO date YYYY-MM-DD
}

/** Pratinjau §3.4 langkah 3 — dipanggil begitu form lengkap, sebelum petani
 *  berkomitmen. */
export function usePratinjauKiriman(params: ParamsPratinjau | null) {
  return useQuery({
    queryKey: ["kiriman", "pratinjau", params],
    queryFn: () =>
      api<KirimanPratinjauResponse>(
        `/api/kiriman/pratinjau?volume_kg=${params!.volumeKg}&lat=${params!.lat}&lng=${params!.lng}&tanggal=${params!.tanggal}`,
      ),
    enabled: params !== null && params.volumeKg > 0 && Boolean(params.tanggal),
    retry: false,
  });
}

export function useBuatKiriman() {
  return useMutation({
    mutationFn: (body: KirimanCreate) =>
      api<KirimanResponse>("/api/kiriman", { method: "POST", body: JSON.stringify(body) }),
  });
}
