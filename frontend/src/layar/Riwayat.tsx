/** Layar Riwayat (§2.5, layar utama Petani) — daftar ikut kirim + kembalian.
 *  Data/hook (useRiwayatSaya) TIDAK diubah — hanya bahasa tampilan (§K12). */

import { Leaf } from "lucide-react";

import type { components } from "@/api/client";
import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import IkonGembok from "@/komponen/IkonGembok";
import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { SkeletonKartu } from "@/komponen/Skeleton";
import { useRiwayatSaya } from "@/hooks/useRiwayat";
import { formatAngka, formatRupiah, formatTanggal } from "@/utils/format";

type StatusPartisipasi = components["schemas"]["StatusPartisipasi"];
type PartisipasiRiwayatOut = components["schemas"]["PartisipasiRiwayatOut"];

const labelStatus: Record<StatusPartisipasi, string> = {
  TERDAFTAR: "Terdaftar",
  TERKUNCI: "Terkunci",
  DIMUAT: "Dimuat",
  SELESAI: "Selesai",
  BATAL: "Batal",
};

/** Bahasa pill 3-nada seragam dengan komponen/BadgeStatus (K12): baik (daun),
 *  netral (kabut), buruk (tanah-liat). */
const kelasStatus: Record<StatusPartisipasi, string> = {
  TERDAFTAR: "bg-daun/15 text-daun",
  TERKUNCI: "bg-tanah-liat/15 text-tanah-liat",
  DIMUAT: "bg-kabut/60 text-tanah/60",
  SELESAI: "bg-daun/15 text-daun",
  BATAL: "bg-tanah-liat/15 text-tanah-liat",
};

export default function Riwayat() {
  const riwayat = useRiwayatSaya();

  return (
    <div className="flex flex-col gap-6">
      <HeaderLayar judul="Riwayat" subjudul="Semua slot yang pernah kamu ikuti" />

      {riwayat.isLoading && <SkeletonKartu jumlah={4} />}

      {riwayat.isError && <KartuGalat pesan="Gagal memuat riwayat." onCobaLagi={() => riwayat.refetch()} />}

      {riwayat.data?.length === 0 && (
        <KeadaanKosong
          pesan="Belum ada riwayat ikut kirim. Cari slot yang sedang dibuka dan ikut kirim →"
          teksAksi="Lihat slot dibuka"
          ke="/beranda"
        />
      )}

      {riwayat.data && riwayat.data.length > 0 && (
        <ul className="flex flex-col gap-3">
          {riwayat.data.map((p) => (
            <BarisRiwayat key={p.id} partisipasi={p} />
          ))}
        </ul>
      )}
    </div>
  );
}

function BarisRiwayat({ partisipasi }: { partisipasi: PartisipasiRiwayatOut }) {
  return (
    <li className="kartu-tonjol flex flex-col gap-3 p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="angka text-base font-semibold text-tanah">{partisipasi.slot_kode}</p>
          <p className="text-keterangan text-tanah/60">{formatTanggal(partisipasi.tanggal_kirim)}</p>
        </div>
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide ${kelasStatus[partisipasi.status]}`}
        >
          {labelStatus[partisipasi.status]}
        </span>
      </div>

      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-daun/10 text-daun">
          <Leaf aria-hidden className="h-4 w-4" strokeWidth={2.25} />
        </span>
        <p className="text-base text-tanah">
          {partisipasi.nama_komoditas} · <span className="angka">{formatAngka(partisipasi.volume_kg)} kg</span>
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-kabut/60 pt-3 text-keterangan text-tanah/80">
        <span className="inline-flex items-center gap-1.5">
          <IkonGembok className="text-tanah/50" />
          Atap <span className="angka font-medium text-tanah">{formatRupiah(partisipasi.harga_atap_per_kg)}/kg</span>
        </span>
        {partisipasi.harga_final_per_kg !== null && partisipasi.harga_final_per_kg !== undefined && (
          <span>
            Final{" "}
            <span className="angka font-medium text-tanah">{formatRupiah(partisipasi.harga_final_per_kg)}/kg</span>
          </span>
        )}
      </div>

      {partisipasi.kembalian_rp > 0 && (
        <div className="flex items-center justify-between gap-3 rounded-lg bg-daun/10 px-3 py-2.5">
          <span className="text-base font-medium text-tanah">Kembalian</span>
          <span className="angka text-lg font-bold text-daun">{formatRupiah(partisipasi.kembalian_rp)}</span>
        </div>
      )}
    </li>
  );
}
