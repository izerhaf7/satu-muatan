/** Beranda Penerima (§9.2 varian) — sapaan + kartu pintasan ke Permintaan (§9.7) dan
 *  Serah Terima. Jumlah pada tiap kartu diambil dari hook yang sudah ada di layar
 *  tujuannya masing-masing (tanpa panggilan API tambahan yang berat). */

import { ChevronRight, ClipboardList, PackageCheck } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";

import { useDaftarPermintaan } from "@/hooks/usePermintaan";
import { useDaftarSlot } from "@/hooks/useSlot";
import { useAuthStore } from "@/stores/authStore";

export default function BerandaPenerima() {
  const pengguna = useAuthStore((s) => s.pengguna);
  const daftarPermintaan = useDaftarPermintaan();
  const daftarJalan = useDaftarSlot("JALAN");

  const permintaanAktif = daftarPermintaan.data?.filter(
    (p) => p.status === "TERBUKA" || p.status === "TERPENUHI_SEBAGIAN",
  ).length;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1 pt-1">
        <p className="text-keterangan font-bold uppercase tracking-wide text-daun">Beranda</p>
        <h1 className="text-judul text-tanah">Halo, {pengguna?.nama ?? "Kamu"}</h1>
        <p className="text-base text-tanah/70">Kelola permintaan komoditas kamu</p>
      </header>

      <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2 lg:items-start">
        <KartuPintasan
          ke="/permintaan"
          ikon={ClipboardList}
          judul="Permintaan"
          keterangan="Ajukan kebutuhan komoditas ke koperasi"
          jumlah={permintaanAktif}
          labelJumlah="aktif"
        />
        <KartuPintasan
          ke="/serah-terima"
          ikon={PackageCheck}
          judul="Serah Terima"
          keterangan="Terima kiriman yang sudah sampai"
          jumlah={daftarJalan.data?.length}
          labelJumlah="dalam perjalanan"
        />
      </div>
    </div>
  );
}

function KartuPintasan({
  ke,
  ikon: Ikon,
  judul,
  keterangan,
  jumlah,
  labelJumlah,
}: {
  ke: string;
  ikon: LucideIcon;
  judul: string;
  keterangan: string;
  jumlah?: number;
  labelJumlah: string;
}) {
  return (
    <Link
      to={ke}
      className="kartu-tonjol flex items-center gap-4 p-4 transition-colors duration-cepat hover:border-daun focus-visible:border-daun"
    >
      <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-daun/10 text-daun">
        <Ikon aria-hidden className="h-6 w-6" strokeWidth={2.25} />
      </span>
      <span className="flex min-w-0 flex-1 flex-col">
        <span className="text-base font-semibold text-tanah">{judul}</span>
        <span className="text-keterangan text-tanah/60">{keterangan}</span>
        {jumlah !== undefined && (
          <span className="angka mt-1 text-keterangan font-semibold text-daun">
            {jumlah} {labelJumlah}
          </span>
        )}
      </span>
      <ChevronRight aria-hidden className="h-5 w-5 shrink-0 text-tanah/40" />
    </Link>
  );
}
