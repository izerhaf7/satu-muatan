/** Dashboard Dampak (§9.10) — 4 kartu (truk-km, emisi, penghematan ongkos, susut
 *  dicegah) + grafik batang bulanan. Kartu `nilai=null` WAJIB tampil "—", jangan
 *  pernah nol yang terlihat seperti hasil hitung (spec §7, aturan kejujuran). */

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import KartuGalat from "@/komponen/KartuGalat";
import KartuMetrik from "@/komponen/KartuMetrik";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { Skeleton, SkeletonAngka } from "@/komponen/Skeleton";
import { useDampakBulanan, useDampakRingkasan } from "@/hooks/useDampak";

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
        <section aria-label="Ringkasan dampak" className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <KartuMetrik
            label="Truk-km dihemat"
            nilai={ringkasan.data.truk_km_dihemat.nilai ?? null}
            satuan={ringkasan.data.truk_km_dihemat.satuan}
            statusSumber={ringkasan.data.truk_km_dihemat.status_sumber}
            rumus={ringkasan.data.truk_km_dihemat.rumus}
            catatanSumber={ringkasan.data.truk_km_dihemat.catatan_sumber}
          />
          <KartuMetrik
            label="Emisi CO₂e dihemat"
            nilai={ringkasan.data.emisi_dihemat_kg_co2.nilai ?? null}
            satuan={ringkasan.data.emisi_dihemat_kg_co2.satuan}
            statusSumber={ringkasan.data.emisi_dihemat_kg_co2.status_sumber}
            rumus={ringkasan.data.emisi_dihemat_kg_co2.rumus}
            catatanSumber={ringkasan.data.emisi_dihemat_kg_co2.catatan_sumber}
          />
          <KartuMetrik
            label="Penghematan ongkos"
            nilai={ringkasan.data.penghematan_ongkos_rp.nilai ?? null}
            satuan={ringkasan.data.penghematan_ongkos_rp.satuan}
            statusSumber={ringkasan.data.penghematan_ongkos_rp.status_sumber}
            rumus={ringkasan.data.penghematan_ongkos_rp.rumus}
            catatanSumber={ringkasan.data.penghematan_ongkos_rp.catatan_sumber}
            tampilan="rupiah"
          />
          <KartuMetrik
            label="Susut dicegah"
            nilai={ringkasan.data.susut_dicegah_kg.nilai ?? null}
            satuan={ringkasan.data.susut_dicegah_kg.satuan}
            statusSumber={ringkasan.data.susut_dicegah_kg.status_sumber}
            rumus={ringkasan.data.susut_dicegah_kg.rumus}
            catatanSumber={ringkasan.data.susut_dicegah_kg.catatan_sumber}
          />
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
