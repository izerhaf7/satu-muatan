/** Layar Buat Slot (§9.3) — tanggal kirim + jam cutoff, pilih tujuan, pratinjau, simpan.
 *  Rombakan §K12: terasa seperti alur bertahap (chip "Langkah N") tapi tetap SATU
 *  halaman scroll — bukan stepper ber-rute. Logika/validasi/hook TIDAK diubah. */

import { type FormEvent, useState } from "react";
import { MapPin } from "lucide-react";
import { useNavigate } from "react-router-dom";

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import InputTeks from "@/komponen/InputTeks";
import KartuGalat from "@/komponen/KartuGalat";
import KotakCentang from "@/komponen/KotakCentang";
import { SkeletonKartu } from "@/komponen/Skeleton";
import { Tabel, Td, Th, Thead } from "@/komponen/Tabel";
import Tombol from "@/komponen/Tombol";
import { useToast } from "@/komponen/Toast";
import { useDaftarPenerima } from "@/hooks/usePenerima";
import { useDaftarPermintaan } from "@/hooks/usePermintaan";
import { useBuatSlot, usePratinjauSlot } from "@/hooks/useSlot";
import { formatAngka, formatRupiah, formatTanggal } from "@/utils/format";

/** Skenario volume dipratinjau (§9.3: "tabel harga/kg pada berbagai skenario volume"). */
const SKENARIO_VOLUME = [300, 800, 2000];

export default function BuatSlot() {
  const navigate = useNavigate();
  const tampilkanToast = useToast();
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
   *  supaya petugas tidak perlu mencentang dua kali untuk hal yang sama. */
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
      {
        onSuccess: () => {
          tampilkanToast("Slot dibuka.");
          navigate("/beranda", { replace: true });
        },
      },
    );
  }

  const bisaSimpan = Boolean(tanggalKirim && jamCutoff && tujuanTerpilih.length > 0);

  return (
    <div className="flex flex-col gap-6 pb-24 lg:pb-0">
      <HeaderLayar judul="Buka slot baru" subjudul="Atur jadwal dan tujuan pengiriman" kembaliKe="/beranda" />

      <form onSubmit={simpan} className="flex flex-col gap-7">
        <section className="flex flex-col gap-3">
          <LangkahLabel nomor={1} label="Jadwal" />
          <div className="grid grid-cols-2 gap-3">
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
          </div>
        </section>

        <section aria-label="Pilih tujuan" className="flex flex-col gap-3">
          <LangkahLabel nomor={2} label="Tujuan" />
          {daftarPenerima.isLoading && <SkeletonKartu jumlah={2} />}
          {daftarPenerima.isError && (
            <KartuGalat pesan="Gagal memuat daftar tujuan." onCobaLagi={() => daftarPenerima.refetch()} />
          )}
          {daftarPenerima.data?.length === 0 && (
            <p className="text-base text-tanah/60">Belum ada penerima terdaftar.</p>
          )}
          <div className="flex flex-col gap-2 lg:grid lg:grid-cols-2 lg:items-start">
            {daftarPenerima.data?.map((p) => {
              const terpilih = tujuanTerpilih.includes(p.id);
              return (
                <label
                  key={p.id}
                  className={`kartu-datar flex min-h-sentuh cursor-pointer items-center gap-3 p-3.5 transition-colors duration-cepat hover:border-daun ${
                    terpilih ? "border-daun bg-daun/5" : ""
                  }`}
                >
                  <input
                    type="checkbox"
                    className="h-5 w-5 shrink-0 accent-daun"
                    checked={terpilih}
                    onChange={() => toggleTujuan(p.id)}
                  />
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-tanah/5 text-tanah/60">
                    <MapPin aria-hidden className="h-4 w-4" />
                  </span>
                  <span className="flex min-w-0 flex-col">
                    <span className="truncate text-base text-tanah">{p.nama}</span>
                    <span className="truncate text-keterangan text-tanah/60">{p.alamat}</span>
                  </span>
                </label>
              );
            })}
          </div>
        </section>

        {daftarPermintaan.data && daftarPermintaan.data.length > 0 && (
          <section className="flex flex-col gap-3">
            <LangkahLabel nomor={3} label="Permintaan" opsional />
            <div className="flex flex-col gap-1 lg:grid lg:grid-cols-2 lg:items-start lg:gap-3">
              {daftarPermintaan.data.map((p) => (
                <KotakCentang
                  key={p.id}
                  label={`${p.nama_penerima} · ${p.nama_komoditas} · ${formatAngka(p.volume_kg)} kg`}
                  keterangan={`Dibutuhkan ${formatTanggal(p.tanggal_dibutuhkan)}`}
                  checked={permintaanTerpilih.includes(p.id)}
                  onChange={() => togglePermintaan(p.id, p.penerima_id)}
                />
              ))}
            </div>
          </section>
        )}

        <section className="flex flex-col gap-3">
          <LangkahLabel nomor={4} label="Pratinjau" />

          <Tombol type="button" varian="sekunder" disabled={tujuanTerpilih.length === 0} sedangProses={pratinjau.isPending} onClick={lihatPratinjau}>
            Lihat pratinjau
          </Tombol>

          {pratinjau.isError && (
            <p role="alert" className="text-keterangan text-tanah-liat">
              Gagal menghitung pratinjau. Coba lagi.
            </p>
          )}

          {pratinjau.data && (
            <div className="flex flex-col gap-3">
              <p className="text-base text-tanah">
                Jarak rute: <span className="angka font-semibold">{formatAngka(pratinjau.data.jarak_km)} km</span>
              </p>
              <Tabel>
                <Thead>
                  <tr>
                    <Th>Volume</Th>
                    <Th>Harga/kg</Th>
                    <Th>Kendaraan</Th>
                  </tr>
                </Thead>
                <tbody>
                  {pratinjau.data.tabel_harga.map((baris) => (
                    <tr key={baris.volume_kg}>
                      <Td className="angka">{formatAngka(baris.volume_kg)} kg</Td>
                      <Td className="angka font-semibold">{formatRupiah(baris.harga_per_kg)}</Td>
                      <Td className="text-keterangan text-tanah/70">{baris.kendaraan.join(" + ")}</Td>
                    </tr>
                  ))}
                </tbody>
              </Tabel>
            </div>
          )}
        </section>

        {buatSlot.isError && (
          <p role="alert" className="text-keterangan text-tanah-liat">
            Gagal menyimpan slot. Coba lagi.
          </p>
        )}

        <div className="fixed inset-x-0 bottom-[calc(3.5rem+env(safe-area-inset-bottom))] z-20 mx-auto max-w-md border-t border-kabut bg-kertas/95 p-4 backdrop-blur-sm lg:static lg:mx-0 lg:max-w-none lg:border-0 lg:bg-transparent lg:p-0 lg:backdrop-blur-none">
          <Tombol type="submit" varian="aksi" className="w-full" disabled={!bisaSimpan} sedangProses={buatSlot.isPending}>
            Simpan slot
          </Tombol>
        </div>
      </form>
    </div>
  );
}

function LangkahLabel({ nomor, label, opsional }: { nomor: number; label: string; opsional?: boolean }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-daun text-keterangan font-bold text-kertas">
        {nomor}
      </span>
      <h2 className="text-subjudul text-tanah">
        {label}
        {opsional && <span className="ml-1.5 text-keterangan font-normal text-tanah/50">(opsional)</span>}
      </h2>
    </div>
  );
}
