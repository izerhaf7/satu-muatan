/** Daftar peserta Detail Slot (§9.4). Baris peserta baru masuk dengan animasi
 *  fade+slide sekali jalan (§9.4 butir 3) — SATU dari dua animasi yang diizinkan
 *  di seluruh aplikasi (yang lain: count-up Harga Berjalan). Peserta yang sudah
 *  ada saat layar pertama dimuat TIDAK animasi, hanya yang muncul dari polling
 *  berikutnya. Dihormati prefers-reduced-motion. */

import { useEffect, useMemo, useRef, useState } from "react";

import type { components } from "@/api/client";
import { formatAngka } from "@/utils/format";

type PartisipasiOut = components["schemas"]["PartisipasiOut"];

interface DaftarPesertaProps {
  partisipasi: PartisipasiOut[];
}

function gerakanDikurangi(): boolean {
  return typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches === true;
}

export default function DaftarPeserta({ partisipasi }: DaftarPesertaProps) {
  const idDikenal = useRef<Set<string>>(new Set());
  const [siapDeteksi, setSiapDeteksi] = useState(false);

  const idBaru = useMemo(() => {
    const set = new Set<string>();
    if (siapDeteksi) {
      for (const p of partisipasi) {
        if (!idDikenal.current.has(p.id)) set.add(p.id);
      }
    }
    return set;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [partisipasi, siapDeteksi]);

  useEffect(() => {
    for (const p of partisipasi) idDikenal.current.add(p.id);
    if (!siapDeteksi) setSiapDeteksi(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [partisipasi]);

  if (partisipasi.length === 0) {
    return <p className="py-4 text-center text-base text-tanah/60">Belum ada petani bergabung.</p>;
  }

  return (
    <ul aria-label="Daftar peserta" className="flex flex-col">
      {partisipasi.map((p) => (
        <BarisPeserta key={p.id} partisipasi={p} baru={idBaru.has(p.id)} />
      ))}
    </ul>
  );
}

function BarisPeserta({ partisipasi, baru }: { partisipasi: PartisipasiOut; baru: boolean }) {
  const [tampil, setTampil] = useState(!baru);

  useEffect(() => {
    if (!baru) return;
    if (gerakanDikurangi()) {
      setTampil(true);
      return;
    }
    const id = requestAnimationFrame(() => setTampil(true));
    return () => cancelAnimationFrame(id);
  }, [baru]);

  return (
    <li
      className="flex items-center justify-between gap-3 border-b border-kabut/60 py-3 transition-all duration-[380ms] ease-out last:border-b-0"
      style={{
        opacity: tampil ? 1 : 0,
        transform: tampil ? "translateY(0)" : "translateY(10px)",
      }}
    >
      <div className="flex flex-col">
        <span className="text-base font-medium text-tanah">{partisipasi.nama_petani}</span>
        <span className="text-sm text-tanah/60">{partisipasi.nama_komoditas}</span>
      </div>
      <span className="angka text-base text-tanah">{formatAngka(partisipasi.volume_kg)} kg</span>
    </li>
  );
}
