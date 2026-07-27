/** Bar kapasitas + petunjuk naik kelas kendaraan (§9.4 butir 4), kartu-tonjol.
 *  Warna berubah sesaat saat `rencana_saat_ini.tier` berganti dibanding polling
 *  sebelumnya — ini PERUBAHAN WARNA berbasis state, bukan animasi CSS (dua animasi
 *  yang diizinkan sudah dipakai di tempat lain: count-up harga & baris peserta baru).
 *  Logika deteksi naik-kelas TIDAK diubah, hanya bahasa tampilannya. */

import { useEffect, useRef, useState } from "react";
import { Truck } from "lucide-react";

import BarKapasitas from "@/komponen/BarKapasitas";
import type { components } from "@/api/client";
import { formatAngka } from "@/utils/format";

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

  return (
    <section aria-label="Kapasitas slot" className="kartu-tonjol flex flex-col gap-3 p-4">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-subjudul text-tanah">Kapasitas</h2>
        <p className="text-keterangan text-tanah/70">{jumlahPeserta} petani sudah bergabung</p>
      </div>

      <BarKapasitas
        volumeKg={volumeKg}
        kapasitasKg={rencana?.kapasitas_total_kg ?? null}
        varian={naikKelas ? "mendekati-batas" : "normal"}
      />

      {rencana && rencana.tier.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {rencana.tier.map((tier) => (
            <span
              key={tier.kode}
              className="inline-flex items-center gap-1.5 rounded-full bg-tanah/5 px-2.5 py-1 text-keterangan font-semibold text-tanah/70"
            >
              <Truck aria-hidden className="h-3.5 w-3.5" />
              {tier.nama} · {formatAngka(tier.kapasitas_kg)} kg
            </span>
          ))}
        </div>
      )}

      {naikKelas && (
        <p className="text-keterangan font-semibold text-tanah-liat" role="status">
          Kendaraan naik kelas ke {rencana?.tier.map((t) => t.nama).join(" + ")}
        </p>
      )}
    </section>
  );
}
