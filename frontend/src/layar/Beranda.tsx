/** Layar Beranda (§9.2) — dispatcher per peran (§2.5). Bilah atas (nama + keluar)
 *  sama untuk ketiga peran; isi di bawahnya berbeda per peran. */

import { useNavigate } from "react-router-dom";

import Tombol from "@/komponen/Tombol";
import { useAuthStore } from "@/stores/authStore";

import BerandaKoperasi from "./beranda/BerandaKoperasi";
import BerandaPenerima from "./beranda/BerandaPenerima";
import BerandaPetani from "./beranda/BerandaPetani";

export default function Beranda() {
  const navigate = useNavigate();
  const pengguna = useAuthStore((s) => s.pengguna);
  const keluar = useAuthStore((s) => s.keluar);

  function handleKeluar() {
    keluar();
    navigate("/masuk", { replace: true });
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col">
      <div className="flex items-center justify-between gap-3 border-b-2 border-kabut px-5 py-3">
        <p className="text-base font-medium text-tanah">{pengguna?.nama ?? "—"}</p>
        <Tombol varian="sekunder" onClick={handleKeluar} className="px-3 text-sm">
          Keluar
        </Tombol>
      </div>
      {pengguna?.peran === "KOPERASI" && <BerandaKoperasi />}
      {pengguna?.peran === "PETANI" && <BerandaPetani />}
      {pengguna?.peran === "PENERIMA" && <BerandaPenerima />}
    </div>
  );
}
