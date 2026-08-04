/** Hook pendukung alamat (K14): autocomplete wilayah & baca alamat dari titik.
 *
 *  Keduanya lewat backend kita sendiri — daftar wilayah hidup di database
 *  (jalan tanpa internet), dan reverse geocoding diproksikan supaya kunci
 *  Google, kalau dipakai, tidak pernah masuk browser. */

import { useQuery } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type WilayahOut = components["schemas"]["WilayahOut"];
type GeokodeOut = components["schemas"]["GeokodeOut"];

/** Autocomplete daerah. Query di-`enabled` mulai 2 huruf, sama dengan server. */
export function useCariWilayah(kataKunci: string) {
  const q = kataKunci.trim();
  return useQuery({
    queryKey: ["wilayah", q],
    queryFn: () => api<WilayahOut[]>(`/api/wilayah/cari?q=${encodeURIComponent(q)}`),
    enabled: q.length >= 2,
    staleTime: 10 * 60 * 1000, // daftar wilayah nyaris tidak pernah berubah
  });
}

/** Alamat dari koordinat. Hasilnya di-cache server, jadi aman dipanggil tiap
 *  kali pin digeser tanpa membebani apa pun. */
export function useGeokodeBalik(titik: { lat: number; lng: number } | null) {
  return useQuery({
    queryKey: ["geokode", titik?.lat, titik?.lng],
    queryFn: () => api<GeokodeOut>(`/api/geokode/balik?lat=${titik!.lat}&lng=${titik!.lng}`),
    enabled: titik !== null,
    staleTime: Infinity,
  });
}
