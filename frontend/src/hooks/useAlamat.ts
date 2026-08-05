/** Hook pendukung alamat (K14): autocomplete wilayah & baca alamat dari titik.
 *
 *  Keduanya lewat backend kita sendiri — daftar wilayah hidup di database
 *  (jalan tanpa internet), dan reverse geocoding diproksikan supaya kunci
 *  Google, kalau dipakai, tidak pernah masuk browser. */

import { useMutation, useQuery } from "@tanstack/react-query";

import { api, type components } from "@/api/client";
import {
  buatPathWilayahAnak,
  type TingkatWilayah,
  type WilayahAnak,
} from "@/komponen/wilayahCascade";
import { buatKunciKoordinat } from "@/layar/kirim-panen/geokodeTitik";

type WilayahOut = components["schemas"]["WilayahOut"];
type GeokodeOut = components["schemas"]["GeokodeOut"];
export type AlamatSaranItem = components["schemas"]["AlamatSaranItemOut"];
export type AlamatSaranList = components["schemas"]["AlamatSaranListOut"];
export type AlamatResolusi = components["schemas"]["AlamatResolusiOut"];

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

export function useCariWilayahAnak(tingkat: TingkatWilayah, indukKode?: string | null) {
  return useQuery({
    queryKey: ["wilayah-anak", tingkat, indukKode ?? null],
    queryFn: () => api<WilayahAnak[]>(buatPathWilayahAnak(tingkat, indukKode)),
    enabled: tingkat === "PROVINSI" || Boolean(indukKode),
    staleTime: 10 * 60 * 1000,
  });
}

/** Alamat dari koordinat. Hasilnya di-cache server, jadi aman dipanggil tiap
 *  kali pin digeser tanpa membebani apa pun. */
export function useGeokodeBalik(titik: { lat: number; lng: number } | null) {
  const kunci = buatKunciKoordinat(titik);
  return useQuery({
    queryKey: ["geokode", titik?.lat, titik?.lng],
    queryFn: async () => ({
      kunci,
      hasil: await api<GeokodeOut>(`/api/geokode/balik?lat=${titik!.lat}&lng=${titik!.lng}`),
    }),
    enabled: titik !== null,
    staleTime: Infinity,
  });
}

export function useSaranAlamat(query: string, aktif = true) {
  const q = query.trim();
  return useQuery({
    queryKey: ["alamat-saran", q],
    queryFn: ({ signal }) =>
      api<AlamatSaranList>("/api/alamat/saran", {
        method: "POST",
        body: JSON.stringify({ query: q }),
        signal,
      }),
    enabled: aktif && Array.from(q).length >= 3,
    staleTime: 30 * 1000,
    retry: false,
  });
}

export function useResolusiAlamat() {
  return useMutation({
    mutationFn: ({ placeId, signal }: { placeId: string; signal?: AbortSignal }) =>
      api<AlamatResolusi>("/api/alamat/resolusi", {
        method: "POST",
        body: JSON.stringify({ place_id: placeId }),
        signal,
      }),
  });
}
