/** Hook autentikasi (§9.1) — masuk nomor HP + PIN, masuk cepat (demo), profil sendiri. */

import { useMutation, useQuery } from "@tanstack/react-query";

import { api, type components } from "@/api/client";
import { useAuthStore } from "@/stores/authStore";

type MasukRequest = components["schemas"]["MasukRequest"];
type MasukDemoRequest = components["schemas"]["MasukDemoRequest"];
type TokenResponse = components["schemas"]["TokenResponse"];
type PenggunaOut = components["schemas"]["PenggunaOut"];

export function useMasuk() {
  const setSesi = useAuthStore((s) => s.setSesi);
  return useMutation({
    mutationFn: (body: MasukRequest) =>
      api<TokenResponse>("/api/auth/masuk", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => setSesi(data.token, data.pengguna),
  });
}

export function useMasukDemo() {
  const setSesi = useAuthStore((s) => s.setSesi);
  return useMutation({
    mutationFn: (body: MasukDemoRequest) =>
      api<TokenResponse>("/api/auth/masuk-demo", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: (data) => setSesi(data.token, data.pengguna),
  });
}

/** Profil pengguna login saat ini. `aktif` biasanya diisi `Boolean(token)`. */
export function useSaya(aktif: boolean) {
  return useQuery({
    queryKey: ["saya"],
    queryFn: () => api<PenggunaOut>("/api/auth/saya"),
    enabled: aktif,
  });
}
