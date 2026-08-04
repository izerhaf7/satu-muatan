/** Layar Muat (§9.5, peran Petugas) — timbang tiap lot, foto, cacat terlihat, QR,
 *  lalu "Selesai muat" memberangkatkan slot (status -> JALAN). Guard peran PETUGAS
 *  sudah terpusat di RuteDenganPeran (App.tsx). */

import { CheckCircle2, Truck } from "lucide-react";

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { SkeletonKartu } from "@/komponen/Skeleton";
import Tombol from "@/komponen/Tombol";
import TombolTautan from "@/komponen/TombolTautan";
import { useDaftarLotSlot, useMuatLot, useSelesaiMuat, useSlotUntukMuat } from "@/hooks/useLot";
import { useParams } from "react-router-dom";

import DaftarJemput from "./muat/DaftarJemput";
import KartuLotMuat from "./muat/KartuLotMuat";

export default function Muat() {
  const { id: slotId } = useParams();

  const slot = useSlotUntukMuat(slotId);
  const daftarLot = useDaftarLotSlot(slotId);
  const muatLot = useMuatLot(slotId);
  const selesaiMuat = useSelesaiMuat(slotId);

  const jumlahLot = daftarLot.data?.length ?? 0;
  // K14: satu lot dianggap beres hanya kalau SUDAH DITIMBANG DAN DIFOTO —
  // progresnya harus mencerminkan syarat berangkat yang sesungguhnya, bukan
  // memberi kesan selesai lalu ditolak server saat menekan "Selesai muat".
  const jumlahSelesai =
    daftarLot.data?.filter((l) => l.berat_aktual_kg != null && Boolean(l.foto_muat)).length ?? 0;
  const semuaSelesaiTimbang = jumlahLot > 0 && jumlahSelesai === jumlahLot;
  const sudahBerangkat = slot.data?.status === "JALAN" || slot.data?.status === "SELESAI";
  const persenSelesai = jumlahLot > 0 ? Math.round((jumlahSelesai / jumlahLot) * 100) : 0;

  return (
    <div className="flex flex-col gap-6">
      <HeaderLayar judul="Muat" subjudul={slot.data?.kode} kembaliKe={slotId ? `/slot/${slotId}` : "/beranda"} />

      {slot.isError && <KartuGalat pesan="Gagal memuat data slot." onCobaLagi={() => slot.refetch()} />}

      {sudahBerangkat && (
        <section className="kartu-tonjol flex flex-col items-center gap-4 border-daun/30 bg-daun/5 p-6 text-center">
          <CheckCircle2 aria-hidden className="h-10 w-10 text-daun" />
          <p className="text-base font-semibold text-tanah">
            Muat selesai. Kiriman sudah {slot.data?.status === "SELESAI" ? "diterima" : "berangkat"}.
          </p>
          <TombolTautan to={`/slot/${slotId}/lacak`} ikon={Truck}>
            Lihat pelacakan
          </TombolTautan>
        </section>
      )}

      {!sudahBerangkat && (
        <>
          {daftarLot.isLoading && <SkeletonKartu jumlah={2} />}
          {daftarLot.isError && <KartuGalat pesan="Gagal memuat daftar lot." onCobaLagi={() => daftarLot.refetch()} />}
          {daftarLot.data?.length === 0 && (
            <KeadaanKosong pesan="Belum ada lot untuk dimuat. Tutup slot ini dahulu di layar Detail Slot." />
          )}

          {slot.data && (
            <DaftarJemput jemput={slot.data.jemput ?? []} namaTitikKumpul={slot.data.titik_kumpul.nama} />
          )}

          {jumlahLot > 0 && (
            <section aria-label="Progres timbang" className="kartu-tonjol flex flex-col gap-2 p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-base font-medium text-tanah">Ditimbang &amp; difoto</p>
                <p className="text-base font-semibold text-tanah">
                  <span className="angka font-bold text-daun">{jumlahSelesai}</span>
                  <span className="text-tanah/50"> dari </span>
                  <span className="angka font-bold">{jumlahLot}</span> lot
                </p>
              </div>
              <div className="h-2.5 w-full overflow-hidden rounded-full bg-kabut/70">
                <div
                  className="h-full rounded-full bg-daun transition-[width] duration-500"
                  style={{ width: `${persenSelesai}%` }}
                />
              </div>
            </section>
          )}

          <section aria-label="Daftar lot" className="flex flex-col gap-4 lg:grid lg:grid-cols-2 lg:items-start">
            {daftarLot.data?.map((lot) => (
              <KartuLotMuat
                key={lot.id}
                lot={lot}
                sedangMenyimpan={muatLot.isPending && muatLot.variables?.lotId === lot.id}
                gagalMenyimpan={muatLot.isError && muatLot.variables?.lotId === lot.id}
                onSimpan={(body) => muatLot.mutate({ lotId: lot.id, body })}
              />
            ))}
          </section>

          {jumlahLot > 0 && (
            <div className="sticky bottom-20 z-10 flex flex-col gap-2 rounded-xl border border-kabut bg-kertas p-3 shadow-sedang">
              {selesaiMuat.isError && (
                <p role="alert" className="text-keterangan text-tanah-liat">
                  Gagal menyelesaikan muat. Pastikan semua lot sudah ditimbang dan difoto, lalu coba lagi.
                </p>
              )}
              {!semuaSelesaiTimbang && (
                <p className="text-keterangan text-tanah/55">
                  Semua lot wajib ditimbang dan difoto sebelum berangkat.
                </p>
              )}
              <Tombol
                type="button"
                varian="aksi"
                ikon={Truck}
                sedangProses={selesaiMuat.isPending}
                disabled={!semuaSelesaiTimbang}
                onClick={() => selesaiMuat.mutate()}
              >
                Selesai muat
              </Tombol>
            </div>
          )}
        </>
      )}
    </div>
  );
}
