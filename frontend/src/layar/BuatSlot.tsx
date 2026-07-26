/** Layar Buat Slot (§9.3) — tanggal kirim + jam cutoff, pilih tujuan, pratinjau, simpan. */

import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import AngkaHarga from "@/komponen/AngkaHarga";
import Tombol from "@/komponen/Tombol";
import InputTeks from "@/komponen/InputTeks";
import { useDaftarPenerima } from "@/hooks/usePenerima";
import { useDaftarPermintaan } from "@/hooks/usePermintaan";
import { useBuatSlot, usePratinjauSlot } from "@/hooks/useSlot";
import { formatAngka, formatTanggal } from "@/utils/format";

/** Skenario volume dipratinjau (§9.3: "tabel harga/kg pada berbagai skenario volume"). */
const SKENARIO_VOLUME = [300, 800, 2000];

export default function BuatSlot() {
  const navigate = useNavigate();
  const [tanggalKirim, setTanggalKirim] = useState("");
  const [jamCutoff, setJamCutoff] = useState("");
  const [tujuanTerpilih, setTujuanTerpilih] = useState<string[]>([]);
  const [permintaanTerpilih, setPermintaanTerpilih] = useState<string[]>([]);

  const daftarPenerima = useDaftarPenerima();
  const daftarPermintaan = useDaftarPermintaan();
  const pratinjau = usePratinjauSlot();
  const buatSlot = useBuatSlot();

  function toggleTujuan(id: string) {
    setTujuanTerpilih((prev) => (prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]));
  }

  /** Pilih permintaan sekaligus pra-pilih penerimanya di daftar tujuan (kalau belum dipilih) —
   *  supaya koperasi tidak perlu mencentang dua kali untuk hal yang sama. */
  function togglePermintaan(permintaanId: string, penerimaId: string) {
    setPermintaanTerpilih((prev) => {
      const sudahTerpilih = prev.includes(permintaanId);
      if (sudahTerpilih) return prev.filter((id) => id !== permintaanId);
      setTujuanTerpilih((prevTujuan) => (prevTujuan.includes(penerimaId) ? prevTujuan : [...prevTujuan, penerimaId]));
      return [...prev, permintaanId];
    });
  }

  function lihatPratinjau() {
    if (tujuanTerpilih.length === 0) return;
    pratinjau.mutate({ tujuan: tujuanTerpilih, skenario_volume: SKENARIO_VOLUME });
  }

  function simpan(e: FormEvent) {
    e.preventDefault();
    if (!tanggalKirim || !jamCutoff || tujuanTerpilih.length === 0) return;
    const cutoffAt = `${tanggalKirim}T${jamCutoff}:00`;
    buatSlot.mutate(
      {
        tanggal_kirim: tanggalKirim,
        cutoff_at: cutoffAt,
        tujuan: tujuanTerpilih,
        ...(permintaanTerpilih.length > 0 ? { permintaan_ids: permintaanTerpilih } : {}),
      },
      { onSuccess: () => navigate("/", { replace: true }) },
    );
  }

  const bisaSimpan = Boolean(tanggalKirim && jamCutoff && tujuanTerpilih.length > 0);

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6 pb-24">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-tanah">Buka slot baru</h1>
        <p className="text-base text-tanah/70">Atur jadwal dan tujuan pengiriman</p>
      </header>

      <form onSubmit={simpan} className="flex flex-col gap-5">
        <InputTeks
          label="Tanggal kirim"
          name="tanggal_kirim"
          type="date"
          value={tanggalKirim}
          onChange={(e) => setTanggalKirim(e.target.value)}
          required
        />
        <InputTeks
          label="Jam cutoff"
          name="jam_cutoff"
          type="time"
          value={jamCutoff}
          onChange={(e) => setJamCutoff(e.target.value)}
          required
        />

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1 text-base font-medium text-tanah">Pilih tujuan</legend>
          {daftarPenerima.isLoading && <p className="text-base text-tanah/60">Memuat daftar tujuan…</p>}
          {daftarPenerima.isError && (
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm text-tanah-liat">Gagal memuat daftar tujuan.</p>
              <Tombol
                type="button"
                varian="sekunder"
                onClick={() => daftarPenerima.refetch()}
                className="px-3 text-sm"
              >
                Coba lagi
              </Tombol>
            </div>
          )}
          {daftarPenerima.data?.length === 0 && (
            <p className="text-base text-tanah/60">Belum ada penerima terdaftar.</p>
          )}
          {daftarPenerima.data?.map((p) => (
            <label
              key={p.id}
              className="flex min-h-sentuh cursor-pointer items-center gap-3 rounded-md border-2 border-kabut px-4"
            >
              <input
                type="checkbox"
                className="h-5 w-5"
                checked={tujuanTerpilih.includes(p.id)}
                onChange={() => toggleTujuan(p.id)}
              />
              <span className="flex flex-col">
                <span className="text-base text-tanah">{p.nama}</span>
                <span className="text-sm text-tanah/60">{p.alamat}</span>
              </span>
            </label>
          ))}
        </fieldset>

        {daftarPermintaan.data && daftarPermintaan.data.length > 0 && (
          <fieldset className="flex flex-col gap-2">
            <legend className="mb-1 text-base font-medium text-tanah">Penuhi permintaan dapur (opsional)</legend>
            {daftarPermintaan.data.map((p) => (
              <label
                key={p.id}
                className="flex min-h-sentuh cursor-pointer items-center gap-3 rounded-md border-2 border-kabut px-4"
              >
                <input
                  type="checkbox"
                  className="h-5 w-5"
                  checked={permintaanTerpilih.includes(p.id)}
                  onChange={() => togglePermintaan(p.id, p.penerima_id)}
                />
                <span className="flex flex-col">
                  <span className="text-base text-tanah">
                    {p.nama_penerima} · {p.nama_komoditas} · {formatAngka(p.volume_kg)} kg
                  </span>
                  <span className="text-sm text-tanah/60">Dibutuhkan {formatTanggal(p.tanggal_dibutuhkan)}</span>
                </span>
              </label>
            ))}
          </fieldset>
        )}

        <Tombol
          type="button"
          varian="sekunder"
          onClick={lihatPratinjau}
          disabled={tujuanTerpilih.length === 0 || pratinjau.isPending}
        >
          {pratinjau.isPending ? "Menghitung…" : "Lihat pratinjau"}
        </Tombol>

        {pratinjau.isError && (
          <p role="alert" className="text-sm text-tanah-liat">
            Gagal menghitung pratinjau. Coba lagi.
          </p>
        )}

        {pratinjau.data && (
          <section aria-label="Pratinjau slot" className="flex flex-col gap-3 rounded-lg border-2 border-kabut p-4">
            <p className="text-base text-tanah">
              Jarak rute: <span className="angka font-semibold">{formatAngka(pratinjau.data.jarak_km)} km</span>
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-base">
                <thead>
                  <tr className="border-b-2 border-kabut text-sm text-tanah/60">
                    <th className="py-2 pr-3 font-medium">Volume</th>
                    <th className="py-2 pr-3 font-medium">Harga/kg</th>
                    <th className="py-2 font-medium">Kendaraan</th>
                  </tr>
                </thead>
                <tbody>
                  {pratinjau.data.tabel_harga.map((baris) => (
                    <tr key={baris.volume_kg} className="border-b border-kabut/60">
                      <td className="angka py-2 pr-3">{formatAngka(baris.volume_kg)} kg</td>
                      <td className="py-2 pr-3">
                        <AngkaHarga nilai={baris.harga_per_kg} ukuran="kecil" />
                      </td>
                      <td className="py-2 text-sm text-tanah/70">{baris.kendaraan.join(" + ")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {buatSlot.isError && (
          <p role="alert" className="text-sm text-tanah-liat">
            Gagal menyimpan slot. Coba lagi.
          </p>
        )}

        <Tombol type="submit" varian="aksi" disabled={!bisaSimpan || buatSlot.isPending}>
          {buatSlot.isPending ? "Menyimpan…" : "Simpan"}
        </Tombol>
      </form>
    </main>
  );
}
