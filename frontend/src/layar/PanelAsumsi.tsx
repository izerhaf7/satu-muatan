/** Panel Asumsi (§9.9) — PEMBEDA UTAMA produk. Semua baris `konfigurasi` &
 *  `tier_kendaraan` yang menggerakkan mesin harga, dengan sumbernya masing-masing.
 *  Mengubah nilai di sini langsung mempengaruhi Beranda, Detail Slot, Dashboard
 *  Dampak, dst. (invalidasi query global — lihat `hooks/useAsumsi.ts`). Guard peran
 *  KOPERASI sudah terpusat di RuteDenganPeran (App.tsx). */

import { SlidersHorizontal } from "lucide-react";

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { SkeletonKartu } from "@/komponen/Skeleton";
import { useToast } from "@/komponen/Toast";
import { useDaftarKonfigurasi, useDaftarTier } from "@/hooks/useAsumsi";

import BarisKonfigurasi from "./panel-asumsi/BarisKonfigurasi";
import TabelTier from "./panel-asumsi/TabelTier";

export default function PanelAsumsi() {
  const konfigurasi = useDaftarKonfigurasi();
  const tier = useDaftarTier();
  const tampilkanToast = useToast();

  function tampilkanKonfirmasi() {
    tampilkanToast("Tersimpan — perhitungan lain ikut diperbarui.");
  }

  return (
    <div className="flex flex-col gap-6">
      <HeaderLayar
        judul="Panel Asumsi"
        subjudul="Setiap angka yang menggerakkan mesin harga, lengkap dengan sumbernya"
      />

      <section aria-label="Konfigurasi" className="flex flex-col gap-2">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-tanah">
          <SlidersHorizontal aria-hidden className="h-5 w-5 text-tanah/60" strokeWidth={2.25} />
          Konfigurasi
        </h2>

        {konfigurasi.isLoading && <SkeletonKartu jumlah={4} />}
        {konfigurasi.isError && (
          <KartuGalat pesan="Gagal memuat konfigurasi." onCobaLagi={() => konfigurasi.refetch()} />
        )}
        {konfigurasi.data && konfigurasi.data.length === 0 && <KeadaanKosong pesan="Belum ada baris konfigurasi." />}
        {konfigurasi.data && konfigurasi.data.length > 0 && (
          <ul className="kartu-datar flex flex-col px-4">
            {konfigurasi.data.map((item) => (
              <BarisKonfigurasi key={item.kunci} item={item} onTersimpan={tampilkanKonfirmasi} />
            ))}
          </ul>
        )}
      </section>

      {tier.isLoading && <SkeletonKartu jumlah={3} />}
      {tier.isError && <KartuGalat pesan="Gagal memuat tier kendaraan." onCobaLagi={() => tier.refetch()} />}
      {tier.data && tier.data.length === 0 && <KeadaanKosong pesan="Belum ada tier kendaraan terdaftar." />}
      {tier.data && tier.data.length > 0 && <TabelTier tiers={tier.data} onTersimpan={tampilkanKonfirmasi} />}
    </div>
  );
}
