/** Pembatas rute per peran — menyatukan 3 varian "halaman khusus peran X"
 *  yang sebelumnya ditulis ulang di Muat/PanelAsumsi/SerahTerima. */

import { ShieldAlert } from "lucide-react";
import type { ReactNode } from "react";

import KeadaanKosong from "@/komponen/KeadaanKosong";
import { useAuthStore } from "@/stores/authStore";

const LABEL: Record<string, string> = {
  KOPERASI: "pengurus koperasi",
  PETANI: "petani",
  PENERIMA: "dapur penerima",
};

export default function RuteDenganPeran({ peran, children }: { peran: string[]; children: ReactNode }) {
  const pengguna = useAuthStore((s) => s.pengguna);
  if (pengguna && !peran.includes(pengguna.peran)) {
    return (
      <KeadaanKosong
        ikon={<ShieldAlert aria-hidden className="h-10 w-10 text-tanah/30" />}
        pesan={`Halaman ini khusus ${peran.map((p) => LABEL[p] ?? p).join(" / ")}.`}
        teksAksi="Kembali ke Beranda"
        ke="/beranda"
      />
    );
  }
  return <>{children}</>;
}
