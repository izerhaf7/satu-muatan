/** Daftar nomor resi (Lot.kode_qr) — dipakai di kartu ringkas (Beranda, Riwayat,
 *  kartu muat) DAN di layar Detail Slot. Setiap kode bisa disalin satu tombol,
 *  supaya petani/petugas gampang membagikannya ke penerima. */

import { useState, type MouseEvent } from "react";
import { Check, Copy } from "lucide-react";

import type { components } from "@/api/client";
import { useToast } from "@/komponen/Toast";

type ResiLotRingkasOut = components["schemas"]["ResiLotRingkasOut"];

interface RingkasanResiProps {
  resi: ResiLotRingkasOut[] | undefined;
}

export default function RingkasanResi({ resi }: RingkasanResiProps) {
  if (!resi || resi.length === 0) return null;

  return (
    <div className="flex w-full flex-col gap-1.5 rounded-lg bg-tanah/5 px-3 py-2.5">
      <p className="text-keterangan font-semibold text-tanah/70">Nomor resi</p>
      <ul className="flex flex-col gap-1.5">
        {resi.map((item) => (
          <BarisResi key={item.lot_id} kodeQr={item.kode_qr} />
        ))}
      </ul>
    </div>
  );
}

function BarisResi({ kodeQr }: { kodeQr: string }) {
  const tampilkanToast = useToast();
  const [tersalin, setTersalin] = useState(false);

  async function salin(e: MouseEvent) {
    // RingkasanResi kadang dirender di dalam <Link> kartu (KartuSlotDaftar) —
    // tombol ini tidak boleh ikut memicu navigasi kartu.
    e.preventDefault();
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(kodeQr);
    } catch {
      tampilkanToast("Gagal menyalin. Coba tekan lama untuk menyalin manual.", "galat");
      return;
    }
    setTersalin(true);
    tampilkanToast("Nomor resi disalin");
    setTimeout(() => setTersalin(false), 1500);
  }

  return (
    <li className="flex items-center gap-2">
      <span className="angka min-w-0 flex-1 select-all break-all text-keterangan font-bold text-tanah">
        {kodeQr}
      </span>
      <button
        type="button"
        onClick={salin}
        aria-label={`Salin nomor resi ${kodeQr}`}
        className="flex min-h-sentuh min-w-sentuh shrink-0 items-center justify-center rounded-md border border-kabut bg-kertas text-tanah/70 transition-colors duration-cepat hover:border-tanah/30 active:bg-kabut/40"
      >
        {tersalin ? (
          <Check aria-hidden className="h-4 w-4 text-daun" strokeWidth={2.5} />
        ) : (
          <Copy aria-hidden className="h-4 w-4" strokeWidth={2} />
        )}
      </button>
    </li>
  );
}
