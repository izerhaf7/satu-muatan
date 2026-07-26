/** Beranda Koperasi (§9.2) — daftar slot, tombol buka slot baru, ringkasan bulan ini. */

import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import AngkaHarga from "@/komponen/AngkaHarga";
import KartuSlot from "@/komponen/KartuSlot";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import Tombol from "@/komponen/Tombol";
import { useDampakBulanan } from "@/hooks/useDampak";
import { useDaftarSlot } from "@/hooks/useSlot";
import { bulanSaatIni, formatAngka, formatBulan } from "@/utils/format";

export default function BerandaKoperasi() {
  const daftarSlot = useDaftarSlot();
  const dampak = useDampakBulanan();

  const bulanIni = dampak.data?.find((d) => d.bulan === bulanSaatIni()) ?? null;

  return (
    <main className="flex flex-1 flex-col gap-6 px-5 py-6 pb-24">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-tanah">Beranda</h1>
        <p className="text-base text-tanah/70">Slot pengiriman koperasi Anda</p>
      </header>

      <section aria-label="Ringkasan bulan ini" className="rounded-lg border-2 border-kabut p-4">
        <p className="mb-3 text-base font-semibold text-tanah">Ringkasan {formatBulan(bulanSaatIni())}</p>
        {dampak.isLoading && <p className="text-base text-tanah/60">Memuat ringkasan…</p>}
        {dampak.isError && (
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm text-tanah-liat">Ringkasan gagal dimuat.</p>
            <Tombol varian="sekunder" onClick={() => dampak.refetch()} className="px-3 text-sm">
              Coba lagi
            </Tombol>
          </div>
        )}
        {dampak.data && (
          <div className="grid grid-cols-3 gap-3">
            <RingkasanItem label="Kiriman">
              <p className="angka text-lg font-bold text-tanah">
                {bulanIni ? formatAngka(bulanIni.jumlah_kiriman) : "—"}
              </p>
            </RingkasanItem>
            <RingkasanItem label="Hemat">
              <AngkaHarga nilai={bulanIni ? bulanIni.penghematan_rp : null} ukuran="kecil" />
            </RingkasanItem>
            <RingkasanItem label="Truk-km">
              <p className="angka text-lg font-bold text-tanah">
                {bulanIni ? formatAngka(bulanIni.truk_km_dihemat) : "—"}
              </p>
            </RingkasanItem>
          </div>
        )}
      </section>

      <Link
        to="/slot/baru"
        className="flex min-h-sentuh items-center justify-center rounded-md bg-daun px-5 text-base font-semibold text-kertas"
      >
        Buka slot baru
      </Link>

      <section aria-label="Daftar slot" className="flex flex-col gap-3">
        {daftarSlot.isLoading && <p className="text-base text-tanah/60">Memuat slot…</p>}
        {daftarSlot.isError && (
          <div className="flex flex-col items-start gap-3 rounded-lg border-2 border-tanah-liat/40 p-4">
            <p className="text-base text-tanah-liat">Gagal memuat daftar slot.</p>
            <Tombol varian="sekunder" onClick={() => daftarSlot.refetch()}>
              Coba lagi
            </Tombol>
          </div>
        )}
        {daftarSlot.data?.length === 0 && (
          <KeadaanKosong pesan="Belum ada slot." teksAksi="Buka slot pertama" ke="/slot/baru" />
        )}
        {daftarSlot.data?.map((slot) => <KartuSlot key={slot.id} slot={slot} />)}
      </section>
    </main>
  );
}

function RingkasanItem({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5">
      {children}
      <p className="text-sm text-tanah/60">{label}</p>
    </div>
  );
}
