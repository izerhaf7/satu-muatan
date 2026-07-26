/** Rincian ongkos per petani (§9.8) + ringkasan biaya total, harga final/kg,
 *  dan selisih yang ditanggung koperasi (KEPUTUSAN.md K3, domain/harga.py butir 5).
 *  `subsidi_koperasi` negatif = sisa pembulatan ceil per petani, BUKAN subsidi
 *  sungguhan — diberi label kecil "(pembulatan)" supaya tidak menyesatkan. */

import type { ReactNode } from "react";

import type { components } from "@/api/client";
import { formatAngka, formatRupiah } from "@/utils/format";

type OngkosPetaniOut = components["schemas"]["OngkosPetaniOut"];

interface RincianOngkosProps {
  rincian: OngkosPetaniOut[];
  biayaTotal: number | null;
  hargaFinalPerKg: number | null;
  subsidiKoperasi: number;
}

export default function RincianOngkos({ rincian, biayaTotal, hargaFinalPerKg, subsidiKoperasi }: RincianOngkosProps) {
  // formatRupiah tidak menangani minus secara khusus ("Rp-130") — susun manual
  // supaya terbaca wajar ala Indonesia ("-Rp130").
  const tampilanSubsidi =
    subsidiKoperasi < 0 ? `-${formatRupiah(Math.abs(subsidiKoperasi))}` : formatRupiah(subsidiKoperasi);

  return (
    <section aria-label="Rincian ongkos per petani" className="flex flex-col gap-2">
      <h2 className="text-base font-semibold text-tanah">Rincian ongkos per petani</h2>
      <div className="overflow-x-auto rounded-lg border-2 border-kabut">
        <table className="w-full min-w-[560px] border-collapse text-sm">
          <thead>
            <tr className="border-b-2 border-kabut bg-kabut/30 text-left">
              <Th>Petani</Th>
              <Th className="text-right">Volume</Th>
              <Th className="text-right">Harga atap</Th>
              <Th className="text-right">Harga final</Th>
              <Th className="text-right">Tagihan</Th>
              <Th className="text-right">Kembalian</Th>
            </tr>
          </thead>
          <tbody>
            {rincian.map((r) => (
              <tr key={r.partisipasi_id} className="border-b border-kabut last:border-0">
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
                <td colSpan={6} className="p-3 text-center text-tanah/50">
                  Belum ada partisipasi dengan harga final.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <dl className="flex flex-col gap-1.5 rounded-lg border-2 border-kabut p-4 text-sm">
        <BarisRingkasan label="Biaya total">
          {biayaTotal !== null ? formatRupiah(biayaTotal) : "—"}
        </BarisRingkasan>
        <BarisRingkasan label="Harga final/kg">
          {hargaFinalPerKg !== null ? formatRupiah(hargaFinalPerKg) : "—"}
        </BarisRingkasan>
        <BarisRingkasan label="Selisih ditanggung koperasi">
          <span className="flex items-baseline gap-1.5">
            {tampilanSubsidi}
            {subsidiKoperasi < 0 && <span className="text-xs font-normal text-tanah/50">(pembulatan)</span>}
          </span>
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

function Th({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <th className={`p-2 font-semibold text-tanah ${className}`}>{children}</th>;
}

function Td({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <td className={`p-2 text-tanah ${className}`}>{children}</td>;
}
