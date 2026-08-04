/** Hook titik kumpul milik pengguna login — dipakai sebagai pusat awal peta
 *  pemilih tujuan (K13: tujuan bebas, jadi peta perlu titik berangkat). */

import { useQuery } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type TitikKumpulOut = components["schemas"]["TitikKumpulOut"];

export function useTitikKumpulSaya() {
  return useQuery({
    queryKey: ["titik-kumpul", "saya"],
    queryFn: () => api<TitikKumpulOut>("/api/titik-kumpul/saya"),
    staleTime: 5 * 60 * 1000, // jarang berubah
  });
}
