/** Tabel Tier Kendaraan (§9.9) — nama, kapasitas, tarif dasar, tarif/km, sumber,
 *  toggle aktif langsung di baris, dan edit inline untuk angka tarif/kapasitas. */

import { useState, type FormEvent, type ReactNode } from "react";

import BadgeSumber from "@/komponen/BadgeSumber";
import Tombol from "@/komponen/Tombol";
import type { components } from "@/api/client";
import { useUbahTier } from "@/hooks/useAsumsi";
import { formatAngka, formatRupiah } from "@/utils/format";

type TierKendaraanOut = components["schemas"]["TierKendaraanOut"];

interface TabelTierProps {
  tiers: TierKendaraanOut[];
  onTersimpan: () => void;
}

export default function TabelTier({ tiers, onTersimpan }: TabelTierProps) {
  return (
    <section aria-label="Tier kendaraan" className="flex flex-col gap-2">
      <h2 className="text-lg font-semibold text-tanah">Tier kendaraan</h2>
      <div className="overflow-x-auto rounded-lg border-2 border-kabut">
        <table className="w-full min-w-[640px] border-collapse text-sm">
          <thead>
            <tr className="border-b-2 border-kabut bg-kabut/30 text-left">
              <Th>Nama</Th>
              <Th className="text-right">Kapasitas</Th>
              <Th className="text-right">Tarif dasar</Th>
              <Th className="text-right">Tarif/km</Th>
              <Th>Sumber</Th>
              <Th>Aktif</Th>
              <Th aria-hidden="true" />
            </tr>
          </thead>
          <tbody>
            {tiers.map((tier) => (
              <BarisTier key={tier.id} tier={tier} onTersimpan={onTersimpan} />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function BarisTier({ tier, onTersimpan }: { tier: TierKendaraanOut; onTersimpan: () => void }) {
  const [mengedit, setMengedit] = useState(false);
  const [kapasitas, setKapasitas] = useState(String(tier.kapasitas_kg));
  const [tarifDasar, setTarifDasar] = useState(String(tier.tarif_dasar));
  const [tarifPerKm, setTarifPerKm] = useState(String(tier.tarif_per_km));
  const mutasi = useUbahTier();

  function bukaEdit() {
    setKapasitas(String(tier.kapasitas_kg));
    setTarifDasar(String(tier.tarif_dasar));
    setTarifPerKm(String(tier.tarif_per_km));
    setMengedit(true);
  }

  function batalEdit() {
    setMengedit(false);
    mutasi.reset();
  }

  function submitEdit(e: FormEvent) {
    e.preventDefault();
    mutasi.mutate(
      {
        id: tier.id,
        body: {
          kapasitas_kg: Number(kapasitas),
          tarif_dasar: Number(tarifDasar),
          tarif_per_km: Number(tarifPerKm),
        },
      },
      {
        onSuccess: () => {
          setMengedit(false);
          onTersimpan();
        },
      },
    );
  }

  function ubahAktif() {
    mutasi.mutate({ id: tier.id, body: { aktif: !tier.aktif } }, { onSuccess: () => onTersimpan() });
  }

  return (
    <>
      <tr className="border-b border-kabut align-top last:border-0">
        <Td className="font-medium">{tier.nama}</Td>
        <Td className="angka text-right">{formatAngka(tier.kapasitas_kg)} kg</Td>
        <Td className="angka text-right">{formatRupiah(tier.tarif_dasar)}</Td>
        <Td className="angka text-right">{formatRupiah(tier.tarif_per_km)}</Td>
        <Td>
          <BadgeSumber status={tier.status_sumber} />
        </Td>
        <Td>
          <label className="inline-flex min-h-sentuh items-center gap-2">
            <input
              type="checkbox"
              checked={tier.aktif}
              onChange={ubahAktif}
              disabled={mutasi.isPending}
              className="h-6 w-6 accent-daun"
              aria-label={`Tier ${tier.nama} aktif`}
            />
          </label>
        </Td>
        <Td>
          {!mengedit && (
            <Tombol varian="sekunder" className="px-3 text-sm" onClick={bukaEdit}>
              Ubah
            </Tombol>
          )}
        </Td>
      </tr>
      {mengedit && (
        <tr className="border-b border-kabut">
          <td colSpan={7} className="p-3">
            <form onSubmit={submitEdit} className="flex flex-col gap-3 rounded-md border-2 border-kabut p-3">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <label className="flex flex-col gap-1.5">
                  <span className="text-sm font-medium text-tanah">Kapasitas (kg)</span>
                  <input
                    type="number"
                    inputMode="numeric"
                    min={1}
                    value={kapasitas}
                    onChange={(e) => setKapasitas(e.target.value)}
                    className="min-h-sentuh rounded-md border-2 border-kabut bg-kertas px-4 text-base text-tanah focus:border-daun"
                  />
                </label>
                <label className="flex flex-col gap-1.5">
                  <span className="text-sm font-medium text-tanah">Tarif dasar (Rp)</span>
                  <input
                    type="number"
                    inputMode="numeric"
                    min={1}
                    value={tarifDasar}
                    onChange={(e) => setTarifDasar(e.target.value)}
                    className="min-h-sentuh rounded-md border-2 border-kabut bg-kertas px-4 text-base text-tanah focus:border-daun"
                  />
                </label>
                <label className="flex flex-col gap-1.5">
                  <span className="text-sm font-medium text-tanah">Tarif/km (Rp)</span>
                  <input
                    type="number"
                    inputMode="numeric"
                    min={1}
                    value={tarifPerKm}
                    onChange={(e) => setTarifPerKm(e.target.value)}
                    className="min-h-sentuh rounded-md border-2 border-kabut bg-kertas px-4 text-base text-tanah focus:border-daun"
                  />
                </label>
              </div>
              <div className="flex items-center gap-2">
                <Tombol type="submit" disabled={mutasi.isPending}>
                  {mutasi.isPending ? "Menyimpan…" : "Simpan"}
                </Tombol>
                <Tombol type="button" varian="sekunder" onClick={batalEdit}>
                  Batal
                </Tombol>
              </div>
              {mutasi.isError && (
                <p role="alert" className="text-sm text-tanah-liat">
                  Gagal menyimpan — periksa kembali nilainya.
                </p>
              )}
            </form>
          </td>
        </tr>
      )}
    </>
  );
}

function Th({ children, className = "" }: { children?: ReactNode; className?: string }) {
  return <th className={`p-2 font-semibold text-tanah ${className}`}>{children}</th>;
}

function Td({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <td className={`p-2 text-tanah ${className}`}>{children}</td>;
}
