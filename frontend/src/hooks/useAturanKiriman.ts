/** Hook aturan kiriman (K14) — ambang volume & jarak yang berlaku saat ini.
 *
 *  Nilainya tetap milik tabel `konfigurasi` di server; hook ini hanya membawanya
 *  ke layar Kirim Panen supaya petani tahu batasnya sebelum menekan tombol.
 *  Jangan pernah menyalin angkanya sebagai konstanta di frontend. */

import { useQuery } from "@tanstack/react-query";

import { api, type components } from "@/api/client";

type AturanKirimanOut = components["schemas"]["AturanKirimanOut"];

export function useAturanKiriman() {
  return useQuery({
    queryKey: ["aturan-kiriman"],
    queryFn: () => api<AturanKirimanOut>("/api/aturan-kiriman"),
    staleTime: 5 * 60 * 1000, // berubah hanya lewat Panel Asumsi
  });
}
