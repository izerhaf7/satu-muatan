/** Hook daftar komoditas. */

import { useQuery } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type KomoditasOut = components["schemas"]["KomoditasOut"];

export function useKomoditas() {
  return useQuery({
    queryKey: ["komoditas"],
    queryFn: () => api<KomoditasOut[]>("/api/komoditas"),
  });
}
