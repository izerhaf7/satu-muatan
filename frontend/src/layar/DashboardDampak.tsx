/** Dashboard Dampak (§9.10 + v2 §7.1) — EMPAT KARTU SEMBOYAN (Menekan biaya
 *  logistik · Menurunkan emisi · Transparansi perjalanan · Keamanan pangan),
 *  kata & urutan sama dengan Landing (lihat utils/semboyan.ts). Kartu
 *  `nilai=null` WAJIB tampil "—", jangan pernah nol yang terlihat seperti
 *  hasil hitung (spec §7, aturan kejujuran). */

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import KartuGalat from "@/komponen/KartuGalat";
import KartuMetrik from "@/komponen/KartuMetrik";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { Skeleton, SkeletonAngka } from "@/komponen/Skeleton";
import { useDampakBulanan, useDampakRingkasan } from "@/hooks/useDampak";
import { SEMBOYAN, type KunciSemboyan } from "@/utils/semboyan";

import GrafikBulanan from "./dampak/GrafikBulanan";

export default function DashboardDampak() {
  const ringkasan = useDampakRingkasan();
  const bulanan = useDampakBulanan();

  return (
    <div className="flex flex-col gap-6">
      <HeaderLayar
        judul="Dampak"
        subjudul="Manfaat nyata dari mengirim bersama, dihitung dari slot yang sudah selesai"
      />

      {ringkasan.isLoading && (
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <SkeletonAngka className="kartu-datar" />
          <SkeletonAngka className="kartu-datar" />
          <SkeletonAngka className="kartu-datar" />
          <SkeletonAngka className="kartu-datar" />
        </div>
      )}
      {ringkasan.isError && (
        <KartuGalat pesan="Gagal memuat ringkasan dampak." onCobaLagi={() => ringkasan.refetch()} />
      )}

      {ringkasan.data && (
        <section aria-label="Empat kartu semboyan" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {SEMBOYAN.map((semboyan) => {
            const kartu = ringkasan.data[semboyan.kunci as KunciSemboyan];
            return (
              <KartuMetrik
                key={semboyan.kunci}
                label={semboyan.label}
                nilai={kartu.nilai ?? null}
                satuan={kartu.satuan}
                statusSumber={kartu.status_sumber}
                rumus={kartu.rumus}
                catatanSumber={kartu.catatan_sumber}
                subTeks={kartu.sub_teks}
              />
            );
          })}
        </section>
      )}

      {bulanan.isLoading && <Skeleton className="h-[268px] w-full" />}
      {bulanan.isError && <KartuGalat pesan="Gagal memuat grafik bulanan." onCobaLagi={() => bulanan.refetch()} />}
      {bulanan.data && bulanan.data.length === 0 && (
        <KeadaanKosong
          pesan="Belum ada slot selesai. Dampaknya akan muncul di sini begitu pengiriman pertama tuntas."
          teksAksi="Kembali ke Beranda"
          ke="/beranda"
        />
      )}
      {bulanan.data && bulanan.data.length > 0 && <GrafikBulanan data={bulanan.data} />}
    </div>
  );
}
