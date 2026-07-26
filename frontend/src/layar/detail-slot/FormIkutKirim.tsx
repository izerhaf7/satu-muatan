/** Formulir "Ikut kirim" (§9.4 butir 5, §5.5) — pilih komoditas + volume, cek
 *  pratinjau (peringatan dini luapan) sebelum submit sungguhan. Kalau submit
 *  sungguhan tetap kena 409 LUAPAN_KAPASITAS (kondisi berubah sejak pratinjau),
 *  serahkan ke pemanggil lewat `onLuapan` supaya dialog dua pilihan tampil. */

import { useState } from "react";

import Dialog from "@/komponen/Dialog";
import Tombol from "@/komponen/Tombol";
import { useKomoditas } from "@/hooks/useKomoditas";
import { isLuapanKapasitas, useGabungSlot, usePratinjauGabung, type LuapanKapasitasOut } from "@/hooks/useGabung";
import { formatRupiah } from "@/utils/format";

interface FormIkutKirimProps {
  slotId: string;
  terbuka: boolean;
  onTutup: () => void;
  onLuapan: (info: LuapanKapasitasOut) => void;
}

export default function FormIkutKirim({ slotId, terbuka, onTutup, onLuapan }: FormIkutKirimProps) {
  const komoditas = useKomoditas();
  const [komoditasId, setKomoditasId] = useState("");
  const [volumeKg, setVolumeKg] = useState("");
  const pratinjau = usePratinjauGabung(slotId);
  const gabung = useGabungSlot(slotId);

  function reset() {
    setKomoditasId("");
    setVolumeKg("");
    pratinjau.reset();
    gabung.reset();
  }

  function tutupDanReset() {
    reset();
    onTutup();
  }

  const volumeAngka = Number(volumeKg);
  const volumeValid = volumeKg !== "" && volumeAngka > 0;

  function cekHarga() {
    if (!volumeValid) return;
    pratinjau.mutate({ volume_kg: volumeAngka });
  }

  function kirim() {
    if (!komoditasId || !volumeValid) return;
    gabung.mutate(
      { komoditas_id: komoditasId, volume_kg: volumeAngka },
      {
        onError: (error) => {
          if (isLuapanKapasitas(error)) {
            const info = error.body as LuapanKapasitasOut;
            reset();
            onTutup();
            onLuapan(info);
          }
        },
      },
    );
  }

  if (gabung.isSuccess && gabung.data) {
    return (
      <Dialog terbuka={terbuka} onTutup={tutupDanReset} judul="Kamu ikut kirim">
        <div className="flex flex-col gap-4">
          <p className="text-base text-tanah/80">
            Volume kamu sudah terkunci pada harga atap{" "}
            <span className="angka font-semibold text-tanah">{formatRupiah(gabung.data.harga_atap_per_kg)}/kg</span>.
            Harga ini tidak akan pernah naik, apa pun yang terjadi.
          </p>
          <Tombol type="button" varian="aksi" onClick={tutupDanReset}>
            Selesai
          </Tombol>
        </div>
      </Dialog>
    );
  }

  return (
    <Dialog terbuka={terbuka} onTutup={tutupDanReset} judul="Ikut kirim">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="komoditas-gabung" className="text-base font-medium text-tanah">
            Komoditas
          </label>
          <select
            id="komoditas-gabung"
            className="min-h-sentuh rounded-md border-2 border-kabut bg-kertas px-4 text-base text-tanah focus:border-daun"
            value={komoditasId}
            onChange={(e) => setKomoditasId(e.target.value)}
          >
            <option value="">Pilih komoditas…</option>
            {komoditas.data?.map((k) => (
              <option key={k.id} value={k.id}>
                {k.nama}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="volume-gabung" className="text-base font-medium text-tanah">
            Volume (kg)
          </label>
          <input
            id="volume-gabung"
            type="number"
            inputMode="numeric"
            min={1}
            step={1}
            className="min-h-sentuh rounded-md border-2 border-kabut bg-kertas px-4 text-base text-tanah focus:border-daun"
            value={volumeKg}
            onChange={(e) => {
              setVolumeKg(e.target.value);
              pratinjau.reset();
            }}
            placeholder="mis. 300"
          />
        </div>

        <Tombol type="button" varian="sekunder" disabled={!volumeValid || pratinjau.isPending} onClick={cekHarga}>
          {pratinjau.isPending ? "Menghitung…" : "Cek harga"}
        </Tombol>

        {pratinjau.isError && <p className="text-sm text-tanah-liat">Gagal menghitung pratinjau. Coba lagi.</p>}

        {pratinjau.data && (
          <div className="flex flex-col gap-2 rounded-md bg-kabut/40 p-3 text-sm text-tanah/80">
            <p>
              Harga atap kamu kalau gabung sekarang:{" "}
              <span className="angka font-semibold text-tanah">
                {formatRupiah(pratinjau.data.harga_atap_per_kg)}/kg
              </span>
            </p>
            <p>
              Harga berjalan baru untuk semua peserta:{" "}
              <span className="angka font-semibold text-tanah">
                {formatRupiah(pratinjau.data.harga_berjalan_baru_per_kg)}/kg
              </span>
            </p>
            {pratinjau.data.luapan && (
              <p className="font-medium text-tanah-liat">
                {pratinjau.data.pesan ?? "Volume ini akan melebihi kapasitas rencana saat ini."}
              </p>
            )}
          </div>
        )}

        {gabung.isError && !isLuapanKapasitas(gabung.error) && (
          <p role="alert" className="text-sm text-tanah-liat">
            Gagal mengirim. Coba lagi.
          </p>
        )}

        <Tombol type="button" varian="aksi" disabled={!komoditasId || !volumeValid || gabung.isPending} onClick={kirim}>
          {gabung.isPending ? "Mengirim…" : "Ikut kirim"}
        </Tombol>
      </div>
    </Dialog>
  );
}
