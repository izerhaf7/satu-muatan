/** Store sesi masuk (token + pengguna) — persisted ke localStorage.
 *  setToken di api client selalu ikut disinkronkan lewat sini (satu sumber kebenaran). */

import { create } from "zustand";
import { persist } from "zustand/middleware";

import { setToken, type components } from "@/api/client";

type PenggunaOut = components["schemas"]["PenggunaOut"];

interface AuthState {
  token: string | null;
  pengguna: PenggunaOut | null;
  /** true setelah localStorage selesai dibaca — cegah kedipan redirect ke /masuk saat refresh. */
  telahHidrasi: boolean;
  setSesi: (token: string, pengguna: PenggunaOut) => void;
  keluar: () => void;
}

// Catatan: `onRehydrateStorage` dijalankan SINKRON kalau storage-nya sinkron
// (localStorage memang begitu) — yaitu di tengah evaluasi `create(...)`, sebelum
// assignment `useAuthStore` selesai. Referensi ke `useAuthStore` di dalam
// callback itu akan kena TDZ (ReferenceError, tertelan diam-diam oleh persist).
// Makanya `set` ditangkap lewat closure di bawah, bukan lewat nama store-nya.
let setTelahHidrasi: ((v: boolean) => void) | null = null;

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => {
      setTelahHidrasi = (telahHidrasi) => set({ telahHidrasi });
      return {
        token: null,
        pengguna: null,
        telahHidrasi: false,
        setSesi: (token, pengguna) => {
          setToken(token);
          set({ token, pengguna });
        },
        keluar: () => {
          setToken(null);
          set({ token: null, pengguna: null });
        },
      };
    },
    {
      name: "sm-auth",
      partialize: (state) => ({ token: state.token, pengguna: state.pengguna }),
      onRehydrateStorage: () => (state) => {
        if (state?.token) setToken(state.token);
        setTelahHidrasi?.(true);
      },
    },
  ),
);
