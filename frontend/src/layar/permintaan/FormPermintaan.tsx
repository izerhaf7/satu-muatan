/** Form buat permintaan (§9.7 alur Penerima) — komoditas, volume kg, tanggal dibutuhkan. */

import { type FormEvent, useState } from "react";

import InputTeks from "@/komponen/InputTeks";
import Select from "@/komponen/Select";
import Tombol from "@/komponen/Tombol";
import { useToast } from "@/komponen/Toast";
import { useKomoditas } from "@/hooks/useKomoditas";
import { useBuatPermintaan } from "@/hooks/usePermintaan";

interface FormPermintaanProps {
  onSelesai?: () => void;
}

export default function FormPermintaan({ onSelesai }: FormPermintaanProps) {
  const komoditas = useKomoditas();
  const buatPermintaan = useBuatPermintaan();
  const tampilkanToast = useToast();

  const [komoditasId, setKomoditasId] = useState("");
  const [volumeKg, setVolumeKg] = useState("");
  const [tanggalDibutuhkan, setTanggalDibutuhkan] = useState("");

  const bisaSimpan = Boolean(komoditasId && Number(volumeKg) > 0 && tanggalDibutuhkan);

  function simpan(e: FormEvent) {
    e.preventDefault();
    if (!bisaSimpan) return;
    buatPermintaan.mutate(
      { komoditas_id: komoditasId, volume_kg: Number(volumeKg), tanggal_dibutuhkan: tanggalDibutuhkan },
      {
        onSuccess: () => {
          setKomoditasId("");
          setVolumeKg("");
          setTanggalDibutuhkan("");
          tampilkanToast("Permintaan tersimpan.");
          onSelesai?.();
        },
      },
    );
  }

  return (
    <form onSubmit={simpan} className="kartu-tonjol flex flex-col gap-4 p-4">
      <Select
        label="Komoditas"
        id="permintaan-komoditas"
        value={komoditasId}
        onChange={(e) => setKomoditasId(e.target.value)}
        required
      >
        <option value="" disabled>
          Pilih komoditas
        </option>
        {komoditas.data?.map((k) => (
          <option key={k.id} value={k.id}>
            {k.nama}
          </option>
        ))}
      </Select>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="permintaan-volume" className="text-keterangan font-semibold text-tanah">
          Volume (kg)
        </label>
        <div className="relative">
          <input
            id="permintaan-volume"
            name="volume_kg"
            type="number"
            inputMode="numeric"
            min={1}
            value={volumeKg}
            onChange={(e) => setVolumeKg(e.target.value)}
            required
            className="min-h-sentuh w-full rounded-lg border-2 border-kabut bg-kertas px-4 pr-12 text-base text-tanah placeholder:text-tanah/40 transition-colors duration-cepat hover:border-tanah/30 focus:border-daun focus:outline-none focus:ring-2 focus:ring-daun/25"
          />
          <span className="angka pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-base font-medium text-tanah/50">
            kg
          </span>
        </div>
      </div>

      <InputTeks
        label="Tanggal dibutuhkan"
        name="tanggal_dibutuhkan"
        type="date"
        value={tanggalDibutuhkan}
        onChange={(e) => setTanggalDibutuhkan(e.target.value)}
        required
      />

      {buatPermintaan.isError && (
        <p role="alert" className="text-keterangan text-tanah-liat">
          Gagal menyimpan permintaan. Coba lagi.
        </p>
      )}

      <Tombol type="submit" varian="aksi" sedangProses={buatPermintaan.isPending} disabled={!bisaSimpan}>
        Simpan permintaan
      </Tombol>
    </form>
  );
}
