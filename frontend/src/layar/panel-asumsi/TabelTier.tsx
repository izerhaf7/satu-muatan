/** Tabel Tier Kendaraan (§9.9) — nama, kapasitas, tarif dasar, tarif/km, sumber,
 *  toggle aktif sebagai sakelar (role="switch"), dan edit inline untuk angka tarif/kapasitas. */

import { useState, type FormEvent } from "react";
import { Truck } from "lucide-react";

import BadgeSumber from "@/komponen/BadgeSumber";
import InputTeks from "@/komponen/InputTeks";
import { Tabel, Td, Th, Thead } from "@/komponen/Tabel";
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
      <h2 className="flex items-center gap-2 text-lg font-semibold text-tanah">
        <Truck aria-hidden className="h-5 w-5 text-tanah/60" strokeWidth={2.25} />
        Tier kendaraan
      </h2>
      <Tabel className="min-w-[640px] text-sm">
        <Thead>
          <tr>
            <Th>Nama</Th>
            <Th className="text-right">Kapasitas</Th>
            <Th className="text-right">Tarif dasar</Th>
            <Th className="text-right">Tarif/km</Th>
            <Th>Sumber</Th>
            <Th>Aktif</Th>
            <Th aria-hidden="true" />
          </tr>
        </Thead>
        <tbody>
          {tiers.map((tier) => (
            <BarisTier key={tier.id} tier={tier} onTersimpan={onTersimpan} />
          ))}
        </tbody>
      </Tabel>
    </section>
  );
}

function Sakelar({ aktif, disabled, label, onToggle }: { aktif: boolean; disabled?: boolean; label: string; onToggle: () => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={aktif}
      aria-label={label}
      disabled={disabled}
      onClick={onToggle}
      className="flex min-h-sentuh min-w-sentuh items-center justify-center disabled:opacity-50"
    >
      <span
        aria-hidden
        className={`relative inline-flex h-7 w-12 items-center rounded-full transition-colors duration-cepat ${
          aktif ? "bg-daun" : "bg-kabut"
        }`}
      >
        <span
          className={`inline-block h-5 w-5 transform rounded-full bg-kertas shadow-lembut transition-transform duration-cepat ${
            aktif ? "translate-x-6" : "translate-x-1"
          }`}
        />
      </span>
    </button>
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
      <tr>
        <Td className="font-medium">{tier.nama}</Td>
        <Td className="angka text-right">{formatAngka(tier.kapasitas_kg)} kg</Td>
        <Td className="angka text-right">{formatRupiah(tier.tarif_dasar)}</Td>
        <Td className="angka text-right">{formatRupiah(tier.tarif_per_km)}</Td>
        <Td>
          <BadgeSumber status={tier.status_sumber} />
        </Td>
        <Td>
          <Sakelar aktif={tier.aktif} disabled={mutasi.isPending} label={`Tier ${tier.nama} aktif`} onToggle={ubahAktif} />
        </Td>
        <Td>
          {!mengedit && (
            <Tombol varian="sekunder" className="min-h-11 px-3 text-keterangan" onClick={bukaEdit}>
              Ubah
            </Tombol>
          )}
        </Td>
      </tr>
      {mengedit && (
        <tr>
          <Td colSpan={7}>
            <form onSubmit={submitEdit} className="kartu-datar flex flex-col gap-3 p-3">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <InputTeks
                  label="Kapasitas (kg)"
                  type="number"
                  inputMode="numeric"
                  min={1}
                  value={kapasitas}
                  onChange={(e) => setKapasitas(e.target.value)}
                />
                <InputTeks
                  label="Tarif dasar (Rp)"
                  type="number"
                  inputMode="numeric"
                  min={1}
                  value={tarifDasar}
                  onChange={(e) => setTarifDasar(e.target.value)}
                />
                <InputTeks
                  label="Tarif/km (Rp)"
                  type="number"
                  inputMode="numeric"
                  min={1}
                  value={tarifPerKm}
                  onChange={(e) => setTarifPerKm(e.target.value)}
                />
              </div>
              <div className="flex items-center gap-2">
                <Tombol type="submit" className="min-h-11 px-4 text-keterangan" sedangProses={mutasi.isPending}>
                  Simpan
                </Tombol>
                <Tombol type="button" varian="sekunder" className="min-h-11 px-4 text-keterangan" onClick={batalEdit}>
                  Batal
                </Tombol>
              </div>
              {mutasi.isError && (
                <p role="alert" className="text-keterangan text-tanah-liat">
                  Gagal menyimpan — periksa kembali nilainya.
                </p>
              )}
            </form>
          </Td>
        </tr>
      )}
    </>
  );
}
