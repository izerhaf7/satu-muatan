/** Form buat permintaan (§9.7 alur Penerima) — komoditas, volume kg, tanggal dibutuhkan. */

import { type FormEvent, useState } from "react";

import InputTeks from "@/komponen/InputTeks";
import Tombol from "@/komponen/Tombol";
import { useKomoditas } from "@/hooks/useKomoditas";
import { useBuatPermintaan } from "@/hooks/usePermintaan";

interface FormPermintaanProps {
  onSelesai?: () => void;
}

export default function FormPermintaan({ onSelesai }: FormPermintaanProps) {
  const komoditas = useKomoditas();
  const buatPermintaan = useBuatPermintaan();

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
          onSelesai?.();
        },
      },
    );
  }

  return (
    <form onSubmit={simpan} className="flex flex-col gap-4 rounded-lg border-2 border-kabut p-4">
      <div className="flex flex-col gap-1.5">
        <label htmlFor="permintaan-komoditas" className="text-base font-medium text-tanah">
          Komoditas
        </label>
        <select
          id="permintaan-komoditas"
          value={komoditasId}
          onChange={(e) => setKomoditasId(e.target.value)}
          className="min-h-sentuh rounded-md border-2 border-kabut bg-kertas px-4 text-base text-tanah focus:border-daun"
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
        </select>
      </div>

      <InputTeks
        label="Volume (kg)"
        name="volume_kg"
        type="number"
        inputMode="numeric"
        min={1}
        value={volumeKg}
        onChange={(e) => setVolumeKg(e.target.value)}
        required
      />

      <InputTeks
        label="Tanggal dibutuhkan"
        name="tanggal_dibutuhkan"
        type="date"
        value={tanggalDibutuhkan}
        onChange={(e) => setTanggalDibutuhkan(e.target.value)}
        required
      />

      {buatPermintaan.isError && (
        <p role="alert" className="text-sm text-tanah-liat">
          Gagal menyimpan permintaan. Coba lagi.
        </p>
      )}

      <Tombol type="submit" varian="aksi" disabled={!bisaSimpan || buatPermintaan.isPending}>
        {buatPermintaan.isPending ? "Menyimpan…" : "Simpan permintaan"}
      </Tombol>
    </form>
  );
}
