/** Bar kapasitas + petunjuk naik kelas kendaraan (§9.4 butir 4). Warna berubah
 *  sesaat saat `rencana_saat_ini.tier` berganti dibanding polling sebelumnya —
 *  ini PERUBAHAN WARNA berbasis state, bukan animasi CSS (dua animasi yang
 *  diizinkan sudah dipakai di tempat lain: count-up harga & baris peserta baru). */

import { useEffect, useRef, useState } from "react";

import BarKapasitas from "@/komponen/BarKapasitas";
import type { components } from "@/api/client";

type RencanaArmadaOut = components["schemas"]["RencanaArmadaOut"];

interface KapasitasTierBarProps {
  volumeKg: number;
  rencana: RencanaArmadaOut | null | undefined;
  jumlahPeserta: number;
}

const DURASI_SOROT_MS = 6000;

export default function KapasitasTierBar({ volumeKg, rencana, jumlahPeserta }: KapasitasTierBarProps) {
  const tandaTier = rencana ? rencana.tier.map((t) => t.kode).join("+") : null;
  const tandaSebelumnya = useRef<string | null>(null);
  const sudahMulai = useRef(false);
  const [naikKelas, setNaikKelas] = useState(false);

  useEffect(() => {
    if (!sudahMulai.current) {
      sudahMulai.current = true;
      tandaSebelumnya.current = tandaTier;
      return;
    }
    if (tandaTier !== null && tandaSebelumnya.current !== null && tandaTier !== tandaSebelumnya.current) {
      setNaikKelas(true);
      const id = setTimeout(() => setNaikKelas(false), DURASI_SOROT_MS);
      tandaSebelumnya.current = tandaTier;
      return () => clearTimeout(id);
    }
    tandaSebelumnya.current = tandaTier;
  }, [tandaTier]);

  const namaTier = rencana ? rencana.tier.map((t) => t.nama).join(" + ") : null;

  return (
    <section aria-label="Kapasitas slot" className="flex flex-col gap-2">
      <BarKapasitas
        volumeKg={volumeKg}
        kapasitasKg={rencana?.kapasitas_total_kg ?? null}
        varian={naikKelas ? "mendekati-batas" : "normal"}
      />
      <div className="flex items-center justify-between gap-2 text-sm text-tanah/70">
        <p>{jumlahPeserta} petani sudah bergabung</p>
        {namaTier && <p>Kendaraan: {namaTier}</p>}
      </div>
      {naikKelas && (
        <p className="text-sm font-medium text-tanah-liat" role="status">
          Kendaraan naik kelas ke {namaTier}
        </p>
      )}
    </section>
  );
}
