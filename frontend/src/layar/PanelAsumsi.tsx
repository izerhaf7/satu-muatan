/** Panel Asumsi (§9.9) — PEMBEDA UTAMA produk. Semua baris `konfigurasi` &
 *  `tier_kendaraan` yang menggerakkan mesin harga, dengan sumbernya masing-masing.
 *  Mengubah nilai di sini langsung mempengaruhi Beranda, Detail Slot, Dashboard
 *  Dampak, dst. (invalidasi query global — lihat `hooks/useAsumsi.ts`). */

import { useEffect, useRef, useState } from "react";

import KeadaanKosong from "@/komponen/KeadaanKosong";
import Tombol from "@/komponen/Tombol";
import { useDaftarKonfigurasi, useDaftarTier } from "@/hooks/useAsumsi";
import { useAuthStore } from "@/stores/authStore";

import BarisKonfigurasi from "./panel-asumsi/BarisKonfigurasi";
import TabelTier from "./panel-asumsi/TabelTier";

export default function PanelAsumsi() {
  const pengguna = useAuthStore((s) => s.pengguna);
  const konfigurasi = useDaftarKonfigurasi();
  const tier = useDaftarTier();
  const [pesanSukses, setPesanSukses] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => () => clearTimeout(timerRef.current), []);

  function tampilkanKonfirmasi() {
    setPesanSukses("Tersimpan — perhitungan lain ikut diperbarui.");
    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => setPesanSukses(null), 3500);
  }

  if (pengguna && pengguna.peran !== "KOPERASI") {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6">
        <h1 className="text-2xl font-bold text-tanah">Panel Asumsi</h1>
        <KeadaanKosong pesan="Panel asumsi khusus pengurus koperasi." teksAksi="Kembali ke Beranda" ke="/" />
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6 pb-16">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-tanah">Panel Asumsi</h1>
        <p className="text-base text-tanah/70">
          Setiap angka yang menggerakkan mesin harga, lengkap dengan sumbernya. Ubah di sini, layar lain ikut
          diperbarui.
        </p>
      </header>

      {pesanSukses && (
        <div role="status" className="rounded-md border-2 border-daun bg-daun/10 px-4 py-3 text-sm text-daun">
          {pesanSukses}
        </div>
      )}

      <section aria-label="Konfigurasi" className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold text-tanah">Konfigurasi</h2>

        {konfigurasi.isLoading && <p className="text-base text-tanah/60">Memuat konfigurasi…</p>}
        {konfigurasi.isError && (
          <div className="flex flex-col items-start gap-3 rounded-lg border-2 border-tanah-liat/40 p-4">
            <p className="text-base text-tanah-liat">Gagal memuat konfigurasi.</p>
            <Tombol varian="sekunder" onClick={() => konfigurasi.refetch()}>
              Coba lagi
            </Tombol>
          </div>
        )}
        {konfigurasi.data && konfigurasi.data.length === 0 && (
          <KeadaanKosong pesan="Belum ada baris konfigurasi." />
        )}
        {konfigurasi.data && konfigurasi.data.length > 0 && (
          <ul className="flex flex-col rounded-lg border-2 border-kabut px-4">
            {konfigurasi.data.map((item) => (
              <BarisKonfigurasi key={item.kunci} item={item} onTersimpan={tampilkanKonfirmasi} />
            ))}
          </ul>
        )}
      </section>

      {tier.isLoading && <p className="text-base text-tanah/60">Memuat tier kendaraan…</p>}
      {tier.isError && (
        <div className="flex flex-col items-start gap-3 rounded-lg border-2 border-tanah-liat/40 p-4">
          <p className="text-base text-tanah-liat">Gagal memuat tier kendaraan.</p>
          <Tombol varian="sekunder" onClick={() => tier.refetch()}>
            Coba lagi
          </Tombol>
        </div>
      )}
      {tier.data && tier.data.length === 0 && (
        <KeadaanKosong pesan="Belum ada tier kendaraan terdaftar." />
      )}
      {tier.data && tier.data.length > 0 && <TabelTier tiers={tier.data} onTersimpan={tampilkanKonfirmasi} />}
    </main>
  );
}
