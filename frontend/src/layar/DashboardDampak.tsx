/** Dashboard Dampak (§9.10) — 4 kartu (truk-km, emisi, penghematan ongkos, susut
 *  dicegah) + grafik batang bulanan. Kartu `nilai=null` WAJIB tampil "—", jangan
 *  pernah nol yang terlihat seperti hasil hitung (spec §7, aturan kejujuran). */

import KartuMetrik from "@/komponen/KartuMetrik";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import Tombol from "@/komponen/Tombol";
import { useDampakBulanan, useDampakRingkasan } from "@/hooks/useDampak";

import GrafikBulanan from "./dampak/GrafikBulanan";

export default function DashboardDampak() {
  const ringkasan = useDampakRingkasan();
  const bulanan = useDampakBulanan();

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-tanah">Dampak</h1>
        <p className="text-base text-tanah/70">Manfaat nyata dari mengirim bersama, dihitung dari slot yang sudah selesai.</p>
      </header>

      {ringkasan.isLoading && <p className="text-base text-tanah/60">Memuat ringkasan dampak…</p>}
      {ringkasan.isError && (
        <div className="flex flex-col items-start gap-3 rounded-lg border-2 border-tanah-liat/40 p-4">
          <p className="text-base text-tanah-liat">Gagal memuat ringkasan dampak.</p>
          <Tombol varian="sekunder" onClick={() => ringkasan.refetch()}>
            Coba lagi
          </Tombol>
        </div>
      )}

      {ringkasan.data && (
        <section aria-label="Ringkasan dampak" className="grid grid-cols-2 gap-3">
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

      {bulanan.isLoading && <p className="text-base text-tanah/60">Memuat grafik bulanan…</p>}
      {bulanan.isError && (
        <div className="flex flex-col items-start gap-3 rounded-lg border-2 border-tanah-liat/40 p-4">
          <p className="text-base text-tanah-liat">Gagal memuat grafik bulanan.</p>
          <Tombol varian="sekunder" onClick={() => bulanan.refetch()}>
            Coba lagi
          </Tombol>
        </div>
      )}
      {bulanan.data && bulanan.data.length === 0 && (
        <KeadaanKosong
          pesan="Belum ada slot selesai. Dampaknya akan muncul di sini begitu pengiriman pertama tuntas."
          teksAksi="Kembali ke Beranda"
          ke="/"
        />
      )}
      {bulanan.data && bulanan.data.length > 0 && <GrafikBulanan data={bulanan.data} />}
    </main>
  );
}
