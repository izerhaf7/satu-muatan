/** Beranda Petugas (§9.2) — sapaan, ringkasan bulan ini, TUGAS SAYA, dan PAPAN
 *  TUGAS berisi muatan yang bisa diambil.
 *
 *  K13: tombol "Buka slot baru" dihapus. Petugas adalah driver Satu Muatan.
 *  K14: penugasan otomatis diganti papan tugas. K13 menempelkan driver pada
 *  muatan begitu ia lahir, tanpa batas — satu petugas aktif menyerap SELURUH
 *  muatan di sistem dan tidak ada satu pun cara mengubahnya. Sekarang muatan
 *  menunggu diambil, dan satu petugas hanya boleh membawa satu muatan aktif. */

import type { ReactNode } from "react";
import { Truck } from "lucide-react";

import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { Skeleton, SkeletonKartu } from "@/komponen/Skeleton";
import Tombol from "@/komponen/Tombol";
import { ApiError } from "@/api/client";
import { useDampakBulanan } from "@/hooks/useDampak";
import { useLokasiDriver } from "@/hooks/useLokasiDriver";
import { useDaftarSlot, useSlotTersedia, useTerimaTugas } from "@/hooks/useSlot";
import { useAuthStore } from "@/stores/authStore";
import { bulanSaatIni, formatAngka, formatBulan, formatRupiah } from "@/utils/format";

import KartuSlotDaftar from "./KartuSlotDaftar";

export default function BerandaPetugas() {
  const pengguna = useAuthStore((s) => s.pengguna);
  const lokasi = useLokasiDriver(true);
  const daftarSlot = useDaftarSlot();
  const tersedia = useSlotTersedia(lokasi.status === "aktif");
  const terima = useTerimaTugas();
  const dampak = useDampakBulanan();

  const bulanIni = dampak.data?.find((d) => d.bulan === bulanSaatIni()) ?? null;

  const pesanTerima =
    terima.isError && terima.error instanceof ApiError
      ? (terima.error.body as { detail?: string } | null)?.detail ?? "Gagal mengambil tugas."
      : terima.isError
        ? "Gagal mengambil tugas."
        : null;

  return (
    <div className="flex flex-col gap-6 lg:grid lg:grid-cols-2 lg:items-start">
      <header className="flex flex-col gap-1 pt-1 lg:col-span-2">
        <p className="text-keterangan font-bold uppercase tracking-wide text-daun">Beranda</p>
        <h1 className="text-judul text-tanah">Halo, {pengguna?.nama ?? "Bu/Pak"}</h1>
        <p className="text-base text-tanah/70">Muatan yang ditugaskan untuk kamu bawa</p>
      </header>

      <div className="flex flex-col gap-6">
        {dampak.isError ? (
          <KartuGalat pesan="Ringkasan bulan ini gagal dimuat." onCobaLagi={() => dampak.refetch()} />
        ) : (
          <section aria-label="Ringkasan bulan ini" className="kartu-hero flex flex-col gap-3 px-4 py-5 sm:gap-4 sm:p-5">
          <p className="text-keterangan font-bold uppercase tracking-wide text-kertas/70">
            Ringkasan {formatBulan(bulanSaatIni())}
          </p>
          <div
            className="grid grid-cols-3 gap-2 sm:gap-3"
            role={dampak.isLoading ? "status" : undefined}
            aria-label={dampak.isLoading ? "Memuat ringkasan" : undefined}
          >
            <ItemRingkasan label="Kiriman">
              {dampak.isLoading ? (
                <Skeleton className="h-8 w-12 bg-kertas/20" />
              ) : (
                <p className="angka text-[clamp(0.75rem,4.2vw,1.5rem)] font-bold leading-none text-kertas">
                  {bulanIni ? formatAngka(bulanIni.jumlah_kiriman) : "—"}
                </p>
              )}
            </ItemRingkasan>
            <ItemRingkasan label="Hemat">
              {dampak.isLoading ? (
                <Skeleton className="h-8 w-16 bg-kertas/20" />
              ) : (
                <p className="angka text-[clamp(0.75rem,4.2vw,1.5rem)] font-bold leading-none text-kertas">
                  {bulanIni ? formatRupiah(bulanIni.penghematan_rp) : "—"}
                </p>
              )}
            </ItemRingkasan>
            <ItemRingkasan label="Truk-km">
              {dampak.isLoading ? (
                <Skeleton className="h-8 w-12 bg-kertas/20" />
              ) : (
                <p className="angka text-[clamp(0.75rem,4.2vw,1.5rem)] font-bold leading-none text-kertas">
                  {bulanIni ? formatAngka(bulanIni.truk_km_dihemat) : "—"}
                </p>
              )}
            </ItemRingkasan>
          </div>
          </section>
        )}
      </div>

      <section aria-label="Tugas saya" className="flex flex-col gap-3">
        <h2 className="text-subjudul text-tanah">Tugas saya</h2>
        {daftarSlot.isLoading && <SkeletonKartu />}
        {daftarSlot.isError && <KartuGalat pesan="Gagal memuat daftar muatan." onCobaLagi={() => daftarSlot.refetch()} />}
        {daftarSlot.data?.length === 0 && (
          <KeadaanKosong pesan="Belum ada muatan yang kamu bawa. Ambil satu dari papan tugas di bawah." />
        )}
        {daftarSlot.data?.map((slot) => <KartuSlotDaftar key={slot.id} slot={slot} />)}
      </section>

      <section aria-label="Papan tugas" className="flex flex-col gap-3 lg:col-span-2">
        <div className="flex flex-col gap-0.5">
          <h2 className="text-subjudul text-tanah">Tersedia diambil</h2>
          <p className="text-keterangan text-tanah/55">
            Muatan dalam radius 15 km dari lokasi GPS kamu. Satu muatan aktif dalam satu waktu.
          </p>
        </div>

        {lokasi.status === "meminta" && (
          <p role="status" className="text-keterangan text-tanah/65">
            Meminta akses lokasi untuk mencari tugas terdekat…
          </p>
        )}
        {lokasi.status === "ditolak" && (
          <p role="alert" className="text-keterangan font-medium text-tanah-liat">
            Aktifkan GPS untuk melihat tugas terdekat.
          </p>
        )}
        {lokasi.status === "tidak_didukung" && (
          <p role="alert" className="text-keterangan font-medium text-tanah-liat">
            Perangkat atau browser ini tidak mendukung GPS.
          </p>
        )}
        {lokasi.status === "galat" && (
          <p role="alert" className="text-keterangan font-medium text-tanah-liat">
            Lokasi belum terkirim. Periksa izin GPS dan koneksi, lalu coba lagi.
          </p>
        )}

        {pesanTerima && (
          <p role="alert" className="text-keterangan font-medium text-tanah-liat">
            {pesanTerima}
          </p>
        )}

        {tersedia.isLoading && <SkeletonKartu />}
        {tersedia.isError && (
          <KartuGalat pesan="Gagal memuat papan tugas." onCobaLagi={() => tersedia.refetch()} />
        )}
        {lokasi.status === "aktif" && tersedia.data?.length === 0 && (
          <KeadaanKosong pesan="Tidak ada tugas dalam radius 15 km dari lokasi Anda." />
        )}

        <div className="flex flex-col gap-3 lg:grid lg:grid-cols-2 lg:items-start">
          {tersedia.data?.map((slot) => (
            <div key={slot.id} className="flex flex-col gap-2">
              <KartuSlotDaftar slot={slot} />
              <Tombol
                type="button"
                varian="aksi"
                ikon={Truck}
                sedangProses={terima.isPending && terima.variables === slot.id}
                onClick={() => terima.mutate(slot.id)}
              >
                Ambil tugas ini
              </Tombol>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function ItemRingkasan({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex min-w-0 flex-col gap-1 overflow-hidden">
      {children}
      <p className="text-keterangan text-kertas/70">{label}</p>
    </div>
  );
}
