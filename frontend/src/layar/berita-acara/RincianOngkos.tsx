/** Rincian ongkos per petani (§9.8) + ringkasan biaya total, harga final/kg,
 *  dan selisih jaminan atap (KEPUTUSAN.md K3, domain/harga.py butir 5, rename v2 §2).
 *  `selisih_jaminan_atap` negatif = sisa pembulatan ceil per petani, BUKAN subsidi
 *  sungguhan — diberi label kecil "(pembulatan)" supaya tidak menyesatkan. */

import type { ReactNode } from "react";

import { Tabel, Td, Th, Thead } from "@/komponen/Tabel";
import type { components } from "@/api/client";
import { formatAngka, formatRupiah } from "@/utils/format";

type OngkosPetaniOut = components["schemas"]["OngkosPetaniOut"];

interface RincianOngkosProps {
  rincian: OngkosPetaniOut[];
  biayaTotal: number | null;
  hargaFinalPerKg: number | null;
  selisihJaminanAtap: number;
}

export default function RincianOngkos({ rincian, biayaTotal, hargaFinalPerKg, selisihJaminanAtap }: RincianOngkosProps) {
  // formatRupiah tidak menangani minus secara khusus ("Rp-130") — susun manual
  // supaya terbaca wajar ala Indonesia ("-Rp130").
  const tampilanSelisih =
    selisihJaminanAtap < 0 ? `-${formatRupiah(Math.abs(selisihJaminanAtap))}` : formatRupiah(selisihJaminanAtap);

  return (
    <section aria-label="Rincian ongkos per petani" className="flex flex-col gap-2">
      <h2 className="text-base font-semibold text-tanah">Rincian ongkos per petani</h2>
      <Tabel className="min-w-[560px] text-sm">
        <Thead>
          <tr>
            <Th>Petani</Th>
            <Th className="text-right">Volume</Th>
            <Th className="text-right">Harga atap</Th>
            <Th className="text-right">Harga final</Th>
            <Th className="text-right">Tagihan</Th>
            <Th className="text-right">Kembalian</Th>
          </tr>
        </Thead>
        <tbody>
          {rincian.map((r) => (
            <tr key={r.partisipasi_id}>
              <Td>{r.nama_petani}</Td>
              <Td className="angka text-right">{formatAngka(r.volume_kg)} kg</Td>
              <Td className="angka text-right">{formatRupiah(r.harga_atap_per_kg)}</Td>
              <Td className="angka text-right">{formatRupiah(r.harga_final_per_kg)}</Td>
              <Td className="angka text-right">{formatRupiah(r.tagihan_rp)}</Td>
              <Td className="angka text-right">{formatRupiah(r.kembalian_rp)}</Td>
            </tr>
          ))}
          {rincian.length === 0 && (
            <tr>
              <Td colSpan={6} className="text-center text-tanah/50">
                Belum ada partisipasi dengan harga final.
              </Td>
            </tr>
          )}
        </tbody>
      </Tabel>

      <dl className="kartu-datar flex flex-col gap-1.5 p-4 text-sm">
        <BarisRingkasan label="Biaya total">{biayaTotal !== null ? formatRupiah(biayaTotal) : "—"}</BarisRingkasan>
        <BarisRingkasan label="Harga final/kg">
          {hargaFinalPerKg !== null ? formatRupiah(hargaFinalPerKg) : "—"}
        </BarisRingkasan>
        {/* K11: negatif = surplus pembulatan ceil (masuk kas titik kumpul), bukan subsidi */}
        <BarisRingkasan
          label={selisihJaminanAtap > 0 ? "Selisih dijamin platform" : "Sisa pembulatan (masuk kas titik kumpul)"}
        >
          <span className="flex items-baseline gap-1.5">{tampilanSelisih}</span>
        </BarisRingkasan>
      </dl>
    </section>
  );
}

function BarisRingkasan({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <dt className="text-tanah/70">{label}</dt>
      <dd className="angka font-semibold text-tanah">{children}</dd>
    </div>
  );
}
