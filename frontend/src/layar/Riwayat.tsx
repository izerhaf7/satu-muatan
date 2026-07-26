/** Layar Riwayat (§2.5, layar utama Petani) — daftar ikut kirim + kembalian. */

import type { components } from "@/api/client";
import IkonGembok from "@/komponen/IkonGembok";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import Tombol from "@/komponen/Tombol";
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

const kelasStatus: Record<StatusPartisipasi, string> = {
  TERDAFTAR: "bg-daun text-kertas",
  TERKUNCI: "bg-tanah-liat text-kertas",
  DIMUAT: "bg-tanah text-kertas",
  SELESAI: "bg-kabut text-tanah",
  BATAL: "bg-kabut text-tanah/60",
};

export default function Riwayat() {
  const riwayat = useRiwayatSaya();

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6 pb-24">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-tanah">Riwayat</h1>
        <p className="text-base text-tanah/70">Semua slot yang pernah kamu ikuti</p>
      </header>

      {riwayat.isLoading && <p className="text-base text-tanah/60">Memuat riwayat…</p>}

      {riwayat.isError && (
        <div className="flex flex-col items-start gap-3 rounded-lg border-2 border-tanah-liat/40 p-4">
          <p className="text-base text-tanah-liat">Gagal memuat riwayat.</p>
          <Tombol varian="sekunder" onClick={() => riwayat.refetch()}>
            Coba lagi
          </Tombol>
        </div>
      )}

      {riwayat.data?.length === 0 && (
        <KeadaanKosong
          pesan="Belum ada riwayat ikut kirim. Cari slot yang sedang dibuka dan ikut kirim →"
          teksAksi="Lihat slot dibuka"
          ke="/"
        />
      )}

      {riwayat.data && riwayat.data.length > 0 && (
        <ul className="flex flex-col gap-3">
          {riwayat.data.map((p) => (
            <BarisRiwayat key={p.id} partisipasi={p} />
          ))}
        </ul>
      )}
    </main>
  );
}

function BarisRiwayat({ partisipasi }: { partisipasi: PartisipasiRiwayatOut }) {
  return (
    <li className="flex flex-col gap-2 rounded-lg border-2 border-kabut p-4">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="angka text-base font-semibold text-tanah">{partisipasi.slot_kode}</p>
          <p className="text-sm text-tanah/60">{formatTanggal(partisipasi.tanggal_kirim)}</p>
        </div>
        <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-sm font-semibold ${kelasStatus[partisipasi.status]}`}>
          {labelStatus[partisipasi.status]}
        </span>
      </div>

      <p className="text-base text-tanah">
        {partisipasi.nama_komoditas} · <span className="angka">{formatAngka(partisipasi.volume_kg)} kg</span>
      </p>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t-2 border-kabut pt-2 text-sm text-tanah/80">
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
        <p className="angka text-base font-semibold text-daun">Kembalian {formatRupiah(partisipasi.kembalian_rp)}</p>
      )}
    </li>
  );
}
