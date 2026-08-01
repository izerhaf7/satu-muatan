/** Layar Beranda (§9.2) — dispatcher per peran (§2.5). AppShell sudah menyediakan
 *  bilah akun atas + navigasi bawah; layar ini hanya berisi konten per peran. */

import { useAuthStore } from "@/stores/authStore";

import BerandaPetugas from "./beranda/BerandaPetugas";
import BerandaPenerima from "./beranda/BerandaPenerima";
import BerandaPetani from "./beranda/BerandaPetani";

export default function Beranda() {
  const pengguna = useAuthStore((s) => s.pengguna);

  if (pengguna?.peran === "PETUGAS") return <BerandaPetugas />;
  if (pengguna?.peran === "PETANI") return <BerandaPetani />;
  if (pengguna?.peran === "PENERIMA") return <BerandaPenerima />;
  return null;
}
