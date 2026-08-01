/** Beranda Petugas (§9.2) — sapaan, ringkasan bulan ini sebagai kartu-hero,
 *  tombol buka slot baru, dan daftar slot. Data & hook sama persis dengan
 *  sebelum rombakan visual (§K12) — hanya bahasa tampilan yang berubah. */

import { Plus } from "lucide-react";
import type { ReactNode } from "react";

import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { Skeleton, SkeletonKartu } from "@/komponen/Skeleton";
import TombolTautan from "@/komponen/TombolTautan";
import { useDampakBulanan } from "@/hooks/useDampak";
import { useDaftarSlot } from "@/hooks/useSlot";
import { useAuthStore } from "@/stores/authStore";
import { bulanSaatIni, formatAngka, formatBulan, formatRupiah } from "@/utils/format";

import KartuSlotDaftar from "./KartuSlotDaftar";

export default function BerandaPetugas() {
  const pengguna = useAuthStore((s) => s.pengguna);
  const daftarSlot = useDaftarSlot();
  const dampak = useDampakBulanan();

  const bulanIni = dampak.data?.find((d) => d.bulan === bulanSaatIni()) ?? null;

  return (
    <div className="flex flex-col gap-6 lg:grid lg:grid-cols-2 lg:items-start">
      <header className="flex flex-col gap-1 pt-1 lg:col-span-2">
        <p className="text-keterangan font-bold uppercase tracking-wide text-daun">Beranda</p>
        <h1 className="text-judul text-tanah">Halo, {pengguna?.nama ?? "Bu/Pak"}</h1>
        <p className="text-base text-tanah/70">Slot pengiriman titik kumpul kamu</p>
      </header>

      <div className="flex flex-col gap-6">
        {dampak.isError ? (
          <KartuGalat pesan="Ringkasan bulan ini gagal dimuat." onCobaLagi={() => dampak.refetch()} />
        ) : (
          <section aria-label="Ringkasan bulan ini" className="kartu-hero flex flex-col gap-4 p-5">
          <p className="text-keterangan font-bold uppercase tracking-wide text-kertas/70">
            Ringkasan {formatBulan(bulanSaatIni())}
          </p>
          <div
            className="grid grid-cols-3 gap-3"
            role={dampak.isLoading ? "status" : undefined}
            aria-label={dampak.isLoading ? "Memuat ringkasan" : undefined}
          >
            <ItemRingkasan label="Kiriman">
              {dampak.isLoading ? (
                <Skeleton className="h-8 w-12 bg-kertas/20" />
              ) : (
                <p className="angka text-2xl font-bold text-kertas">
                  {bulanIni ? formatAngka(bulanIni.jumlah_kiriman) : "—"}
                </p>
              )}
            </ItemRingkasan>
            <ItemRingkasan label="Hemat">
              {dampak.isLoading ? (
                <Skeleton className="h-8 w-16 bg-kertas/20" />
              ) : (
                <p className="angka text-2xl font-bold text-kertas">
                  {bulanIni ? formatRupiah(bulanIni.penghematan_rp) : "—"}
                </p>
              )}
            </ItemRingkasan>
            <ItemRingkasan label="Truk-km">
              {dampak.isLoading ? (
                <Skeleton className="h-8 w-12 bg-kertas/20" />
              ) : (
                <p className="angka text-2xl font-bold text-kertas">
                  {bulanIni ? formatAngka(bulanIni.truk_km_dihemat) : "—"}
                </p>
              )}
            </ItemRingkasan>
          </div>
          </section>
        )}

        <TombolTautan to="/slot/baru" ikon={Plus} varian="aksi" className="w-full">
          Buka slot baru
        </TombolTautan>
      </div>

      <section aria-label="Daftar slot" className="flex flex-col gap-3">
        <h2 className="text-subjudul text-tanah">Slot kamu</h2>
        {daftarSlot.isLoading && <SkeletonKartu />}
        {daftarSlot.isError && <KartuGalat pesan="Gagal memuat daftar slot." onCobaLagi={() => daftarSlot.refetch()} />}
        {daftarSlot.data?.length === 0 && (
          <KeadaanKosong pesan="Belum ada slot." teksAksi="Buka slot pertama" ke="/slot/baru" />
        )}
        {daftarSlot.data?.map((slot) => <KartuSlotDaftar key={slot.id} slot={slot} />)}
      </section>
    </div>
  );
}

function ItemRingkasan({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      {children}
      <p className="text-keterangan text-kertas/70">{label}</p>
    </div>
  );
}
