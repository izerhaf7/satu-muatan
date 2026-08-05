/** Layar Lacak Resi (K13, peran Penerima) — SATU pintu masuk bagi penerima.
 *
 *  Penerima tidak memesan dan tidak membuka muatan. Dia memegang nomor resi,
 *  mengetiknya di sini, lalu melihat data perjalanan apa adanya: posisi, suhu
 *  & kelembapan sensor, sisa umur simpan, dan bukti muat. Dari sini pula dia
 *  masuk ke serah terima.
 *
 *  "Memegang resi = berhak melihat" — sama seperti surat jalan sungguhan.
 */

import { type FormEvent, useState } from "react";
import { PackageSearch, Search, Thermometer, Truck } from "lucide-react";
import { useNavigate } from "react-router-dom";

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import InputTeks from "@/komponen/InputTeks";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { Skeleton } from "@/komponen/Skeleton";
import Tombol from "@/komponen/Tombol";
import type { components } from "@/api/client";
import { usePerjalananResi } from "@/hooks/usePerjalananResi";
import { useCariLotQr } from "@/hooks/useSerahTerima";
import { formatAngka } from "@/utils/format";

import GrafikSuhu from "./lacak/GrafikSuhu";
import PetaLacak from "./lacak/PetaLacak";
import TimelineLacak from "./lacak/TimelineLacak";
import KartuIndeksMutu from "./serah-terima/KartuIndeksMutu";

type BuktiLotOut = components["schemas"]["BuktiLotOut"];

export default function LacakResi() {
  const navigate = useNavigate();
  const [resi, setResi] = useState("");
  const [hasil, setHasil] = useState<BuktiLotOut | null>(null);
  const cari = useCariLotQr();

  function cariResi(e: FormEvent) {
    e.preventDefault();
    const kode = resi.trim();
    if (!kode) return;
    cari.mutate(kode, { onSuccess: (data) => setHasil(data) });
  }

  return (
    <div className="flex flex-col gap-6">
      <HeaderLayar
        judul="Lacak Resi"
        subjudul="Masukkan nomor resi untuk melihat posisi & kondisi kiriman"
      />

      <form onSubmit={cariResi} className="kartu-datar flex flex-col gap-3 p-4">
        <InputTeks
          label="Nomor resi"
          name="resi"
          value={resi}
          onChange={(e) => setResi(e.target.value)}
          placeholder="mis. LOT-SM-20260805-CKJ-01-01"
        />
        {cari.isError && (
          <p role="alert" className="text-keterangan text-tanah-liat">
            Nomor resi tidak ditemukan. Periksa lagi hurufnya.
          </p>
        )}
        <Tombol type="submit" varian="aksi" ikon={Search} sedangProses={cari.isPending} disabled={!resi.trim()}>
          Lacak
        </Tombol>
      </form>

      {!hasil && !cari.isPending && (
        <KeadaanKosong pesan="Belum ada yang dilacak. Nomor resi ada di surat jalan atau dikirim oleh petugas." />
      )}

      {hasil && <HasilLacak bukti={hasil} onSerahTerima={() => navigate("/serah-terima")} />}
    </div>
  );
}

function HasilLacak({ bukti, onSerahTerima }: { bukti: BuktiLotOut; onSerahTerima: () => void }) {
  const { lot, serah_terima } = bukti;
  const sudahDiserahkan = serah_terima !== null && serah_terima !== undefined;

  // K14: penerima berhak melihat SELURUH perjalanan — timeline, peta, dan grafik
  // suhu — sebelum memutuskan. Sebelumnya dia cuma dapat dua kotak angka.
  const perjalanan = usePerjalananResi(lot.kode_qr);

  const jejak =
    perjalanan.data?.pengiriman.jejak
      .filter((j) => j.lat != null && j.lng != null)
      .map((j) => ({ lat: j.lat as number, lng: j.lng as number })) ?? [];
  const posisiTerakhir = jejak.at(-1);

  return (
    <section aria-label="Hasil pelacakan" className="flex flex-col gap-4">
      <div className="kartu-tonjol flex flex-col gap-3 p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 flex-col">
            <p className="text-subjudul text-tanah">{lot.nama_komoditas}</p>
            <p className="text-keterangan text-tanah/60">dari {lot.nama_petani}</p>
          </div>
          <span className="shrink-0 rounded-full bg-daun/10 px-3 py-1 text-keterangan font-semibold text-daun">
            {sudahDiserahkan ? "Sudah diterima" : "Dalam perjalanan"}
          </span>
        </div>
        <p className="angka text-keterangan text-tanah/50">{lot.kode_qr}</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <KartuAngka
          ikon={Truck}
          label="Volume"
          nilai={lot.berat_aktual_kg != null ? `${formatAngka(lot.berat_aktual_kg)} kg` : "—"}
        />
        <KartuAngka
          ikon={Thermometer}
          label="Mutu saat muat"
          nilai={lot.grade_asal != null ? `Grade ${lot.grade_asal}` : "—"}
        />
      </div>

      {bukti.mutu && <KartuIndeksMutu mutu={bukti.mutu} />}

      {perjalanan.isLoading && <Skeleton className="h-48 w-full" />}

      {perjalanan.data && (
        <>
          <section aria-label="Status pengiriman" className="kartu-tonjol p-4">
            <TimelineLacak timeline={perjalanan.data.pengiriman.timeline} />
          </section>

          {perjalanan.data.tujuan.length > 0 && (
            <section aria-label="Peta perjalanan">
              <PetaLacak
                gudang={{
                  lat: perjalanan.data.titik_kumpul.lat,
                  lng: perjalanan.data.titik_kumpul.lng,
                  label: perjalanan.data.titik_kumpul.nama,
                }}
                tujuan={perjalanan.data.tujuan.map((t, i) => ({
                  lat: t.lat,
                  lng: t.lng,
                  label: `${i + 1}. ${t.nama}`,
                }))}
                posisiTerakhir={posisiTerakhir ? { ...posisiTerakhir, label: "Posisi terakhir" } : null}
                jejak={jejak}
                rutePolyline={perjalanan.data.pengiriman.rute_polyline}
              />
            </section>
          )}

          {perjalanan.data.telemetri.ringkasan && (
            <section aria-label="Suhu perjalanan" className="kartu-tonjol flex flex-col gap-3 p-4">
              <p className="text-keterangan font-bold uppercase tracking-wide text-tanah/50">Suhu sepanjang jalan</p>
              <GrafikSuhu telemetri={perjalanan.data.telemetri} />
            </section>
          )}
        </>
      )}

      {!sudahDiserahkan && (
        <Tombol type="button" varian="aksi" ikon={PackageSearch} onClick={onSerahTerima}>
          Lanjut ke Serah Terima
        </Tombol>
      )}

      <p className="text-keterangan text-kabut">
        Data perjalanan berasal dari simulasi sensor — sensor fisik menyusul.
      </p>
    </section>
  );
}

function KartuAngka({
  ikon: Ikon,
  label,
  nilai,
}: {
  ikon: typeof Truck;
  label: string;
  nilai: string;
}) {
  return (
    <div className="kartu-datar flex flex-col gap-1 p-3.5">
      <span className="flex items-center gap-1.5 text-keterangan text-tanah/60">
        <Ikon aria-hidden className="h-4 w-4" />
        {label}
      </span>
      <span className="angka text-subjudul font-semibold text-tanah">{nilai}</span>
    </div>
  );
}
