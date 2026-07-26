/** Angka rupiah dengan animasi count-up/count-down (spec §9.4 butir 1, §10).
 *  SATU dari dua animasi yang diizinkan di seluruh aplikasi (yang lain: baris peserta
 *  baru di DaftarPeserta). Pakai HANYA untuk Harga Berjalan di Detail Slot — Harga Atap
 *  tidak boleh animasi (nilainya terkunci, lihat AngkaHarga biasa untuk itu).
 *
 *  Animasi via requestAnimationFrame ~600ms, tabular-nums (mewarisi kelas `.angka`)
 *  supaya digit tidak bergeser. Dihormati prefers-reduced-motion: langsung loncat
 *  ke nilai akhir tanpa animasi. */

import { useEffect, useRef, useState } from "react";

import { formatRupiah } from "@/utils/format";

export type UkuranAngkaHarga = "kecil" | "sedang" | "besar";

interface AngkaCountUpProps {
  nilai: number | null;
  ukuran?: UkuranAngkaHarga;
  satuan?: string;
  className?: string;
}

const kelasUkuran: Record<UkuranAngkaHarga, string> = {
  kecil: "text-lg",
  sedang: "text-2xl",
  besar: "text-4xl",
};

const DURASI_ANIMASI_MS = 600;

function gerakanDikurangi(): boolean {
  return typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true;
}

export default function AngkaCountUp({ nilai, ukuran = "besar", satuan, className = "" }: AngkaCountUpProps) {
  const [tampil, setTampil] = useState<number | null>(nilai);
  const [turun, setTurun] = useState(false);
  const nilaiSebelumnya = useRef<number | null>(nilai);
  const nilaiTertinggi = useRef<number | null>(nilai);
  const frameId = useRef<number | null>(null);

  useEffect(() => {
    if (nilai === null) {
      setTampil(null);
      nilaiSebelumnya.current = null;
      return;
    }

    if (nilaiTertinggi.current === null || nilai > nilaiTertinggi.current) {
      nilaiTertinggi.current = nilai;
      setTurun(false);
    } else if (nilai < nilaiTertinggi.current) {
      setTurun(true);
    }

    const dari = nilaiSebelumnya.current;
    if (dari === null || dari === nilai || gerakanDikurangi()) {
      setTampil(nilai);
      nilaiSebelumnya.current = nilai;
      return;
    }

    const mulaiPada = performance.now();
    const tujuan = nilai;

    function langkah(sekarang: number) {
      const progres = Math.min(1, (sekarang - mulaiPada) / DURASI_ANIMASI_MS);
      const halus = 1 - (1 - progres) ** 3; // ease-out cubic
      setTampil(Math.round(dari! + (tujuan - dari!) * halus));
      if (progres < 1) {
        frameId.current = requestAnimationFrame(langkah);
      } else {
        nilaiSebelumnya.current = tujuan;
      }
    }
    frameId.current = requestAnimationFrame(langkah);

    return () => {
      if (frameId.current !== null) cancelAnimationFrame(frameId.current);
    };
  }, [nilai]);

  return (
    <span className={`angka inline-flex items-baseline gap-2 font-bold text-tanah ${kelasUkuran[ukuran]} ${className}`}>
      <span>
        {tampil === null ? "—" : formatRupiah(tampil)}
        {satuan && tampil !== null && <span className="ml-1 text-base font-normal text-tanah/70">{satuan}</span>}
      </span>
      {turun && tampil !== null && (
        <span aria-hidden="true" className="text-xl font-bold text-daun">
          ↓
        </span>
      )}
    </span>
  );
}
