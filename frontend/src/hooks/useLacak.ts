/** Hook layar Lacak (§9.6) — timeline, GPS driver, status, dan telemetri. */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type SlotDetailOut = components["schemas"]["SlotDetailOut"];
type PengirimanOut = components["schemas"]["PengirimanOut"];
type TelemetriOut = components["schemas"]["TelemetriOut"];
type StatusPengirimanRequest = components["schemas"]["StatusPengirimanRequest"];
type SensorNodeOut = components["schemas"]["SensorNodeOut"];

const INTERVAL_POLL_MS = 3000; // spec §3.1: polling 3 detik, bukan WebSocket.

/** Info slot (kode, titik kumpul, daftar tujuan) — konteks header + titik peta. */
export function useSlotUntukLacak(slotId: string | undefined) {
  return useQuery({
    queryKey: ["slot", slotId, "ringkas-lacak"],
    queryFn: () => api<SlotDetailOut>(`/api/slot/${slotId}`),
    enabled: Boolean(slotId),
  });
}

/** Timeline + estimasi tiba + jejak posisi. Poll 3 detik selama belum TIBA. */
export function usePengirimanSlot(slotId: string | undefined) {
  return useQuery({
    queryKey: ["slot", slotId, "pengiriman"],
    queryFn: () => api<PengirimanOut>(`/api/slot/${slotId}/pengiriman`),
    enabled: Boolean(slotId),
    refetchInterval: (query) => (query.state.data?.timeline.tiba ? false : INTERVAL_POLL_MS),
  });
}

/** Telemetri suhu/kelembapan (spec v2 §5) — SIMULASI berlabel. Poll 3 detik
 *  selama belum TIBA (sampel bertambah per interval). */
export function useTelemetriSlot(slotId: string | undefined, sudahTiba: boolean) {
  return useQuery({
    queryKey: ["slot", slotId, "telemetri"],
    queryFn: () => api<TelemetriOut>(`/api/lacak/${slotId}/telemetri`),
    enabled: Boolean(slotId),
    refetchInterval: sudahTiba ? false : INTERVAL_POLL_MS,
  });
}

export function useUbahStatusPengiriman(slotId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ pengirimanId, status, koordinat }: { pengirimanId: string; status: StatusPengirimanRequest["status"]; koordinat?: { lat: number; lng: number } }) =>
      api<PengirimanOut>(`/api/pengiriman/${pengirimanId}/status`, {
        method: "POST",
        body: JSON.stringify({ status, koordinat }),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["slot", slotId, "pengiriman"] });
      void queryClient.invalidateQueries({ queryKey: ["slot", slotId, "telemetri"] });
    },
  });
}

export function useCatatPosisi(slotId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ pengirimanId, lat, lng, akurasi_m, waktu }: { pengirimanId: string; lat: number; lng: number; akurasi_m?: number; waktu?: string }) =>
      api<PengirimanOut>(`/api/pengiriman/${pengirimanId}/posisi`, {
        method: "POST",
        body: JSON.stringify({ lat, lng, akurasi_m, waktu }),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["slot", slotId, "pengiriman"] });
      void queryClient.invalidateQueries({ queryKey: ["slot", slotId, "telemetri"] });
    },
  });
}

export function useTetapkanSensorNode() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ slotId, node_path }: { slotId: string; node_path: string }) =>
      api<SensorNodeOut>(`/api/slot/${slotId}/sensor-node`, {
        method: "PUT",
        body: JSON.stringify({ node_path }),
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["slot"] });
    },
  });
}
