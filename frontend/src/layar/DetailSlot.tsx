/** Layar Detail Slot (§9.4) — LAYAR UTAMA DEMO. Harga berjalan turun hidup-hidup
 *  di sebelah harga atap yang diam terkunci; juri paham seluruh produk dalam
 *  hitungan detik tanpa penjelasan. Dipoll 3 detik (useDetailSlot). Logika/hook/
 *  polling/pratinjau TIDAK diubah sama sekali — rombakan ini murni visual (§K12). */

import { useState } from "react";
import { useParams } from "react-router-dom";

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { SkeletonAngka, SkeletonKartu } from "@/komponen/Skeleton";
import Tombol from "@/komponen/Tombol";
import { useDetailSlot } from "@/hooks/useDetailSlot";
import type { LuapanKapasitasOut } from "@/hooks/useGabung";
import { useAuthStore } from "@/stores/authStore";

import DaftarPeserta from "./detail-slot/DaftarPeserta";
import DialogLuapanKapasitas from "./detail-slot/DialogLuapanKapasitas";
import FormIkutKirim from "./detail-slot/FormIkutKirim";
import HargaBerjalanHero from "./detail-slot/HargaBerjalanHero";
import HeaderDetailSlot from "./detail-slot/HeaderDetailSlot";
import KapasitasTierBar from "./detail-slot/KapasitasTierBar";
import KartuAtapSaya from "./detail-slot/KartuAtapSaya";
import PanelTutupSlot from "./detail-slot/PanelTutupSlot";
import RingkasanPenutupan from "./detail-slot/RingkasanPenutupan";

export default function DetailSlot() {
  const { id } = useParams();
  const pengguna = useAuthStore((s) => s.pengguna);
  const detail = useDetailSlot(id);
  const [formTerbuka, setFormTerbuka] = useState(false);
  const [luapanInfo, setLuapanInfo] = useState<LuapanKapasitasOut | null>(null);

  if (!id) {
    return (
      <div className="flex flex-col gap-6">
        <HeaderLayar judul="Slot" kembaliKe="/beranda" />
        <KeadaanKosong pesan="Slot tidak ditemukan." teksAksi="Kembali ke Beranda" ke="/beranda" />
      </div>
    );
  }

  const atapSaya =
    pengguna?.peran === "PETANI" &&
    detail.data?.status === "DIBUKA" &&
    detail.data?.atap_saya_per_kg !== null &&
    detail.data?.atap_saya_per_kg !== undefined;

  const tampilkanCtaIkutKirim =
    pengguna?.peran === "PETANI" &&
    detail.data?.status === "DIBUKA" &&
    (detail.data?.atap_saya_per_kg === null || detail.data?.atap_saya_per_kg === undefined);

  return (
    <div className={`flex flex-col gap-6 ${tampilkanCtaIkutKirim ? "pb-24" : ""}`}>
      {detail.data ? (
        <HeaderDetailSlot slot={detail.data} />
      ) : (
        <HeaderLayar judul="Detail slot" kembaliKe="/beranda" />
      )}

      {detail.isLoading && (
        <div className="flex flex-col gap-6">
          <SkeletonAngka className="kartu-hero" />
          <SkeletonKartu jumlah={4} />
        </div>
      )}

      {detail.isError && <KartuGalat pesan="Gagal memuat detail slot." onCobaLagi={() => detail.refetch()} />}

      {detail.data && (
        <>
          {detail.data.status === "DIBUKA" && (
            <div className="overflow-hidden rounded-xl shadow-sedang">
              <HargaBerjalanHero hargaPerKg={detail.data.harga_berjalan_per_kg ?? null} />
              {atapSaya && (
                <KartuAtapSaya
                  atapPerKg={detail.data.atap_saya_per_kg!}
                  hematPerKg={detail.data.hemat_saya_per_kg ?? null}
                  volumeSayaKg={detail.data.partisipasi
                    .filter((p) => p.petani_id === pengguna!.id)
                    .reduce((total, p) => total + p.volume_kg, 0)}
                />
              )}
            </div>
          )}

          <KapasitasTierBar
            volumeKg={detail.data.volume_total_kg}
            rencana={detail.data.rencana_saat_ini}
            jumlahPeserta={detail.data.partisipasi.length}
          />

          <section aria-label="Peserta" className="flex flex-col gap-2">
            <h2 className="text-subjudul text-tanah">Peserta</h2>
            <DaftarPeserta partisipasi={detail.data.partisipasi} />
          </section>

          {detail.data.status !== "DIBUKA" && pengguna && (
            <RingkasanPenutupan slot={detail.data} peran={pengguna.peran} penggunaId={pengguna.id} />
          )}

          {pengguna?.peran === "KOPERASI" && detail.data.status === "DIBUKA" && (
            <PanelTutupSlot slotId={detail.data.id} />
          )}

          {tampilkanCtaIkutKirim && (
            <div className="fixed inset-x-0 bottom-[calc(3.5rem+env(safe-area-inset-bottom))] z-20 mx-auto max-w-md border-t border-kabut bg-kertas/95 p-4 backdrop-blur-sm">
              <Tombol type="button" varian="aksi" className="w-full" onClick={() => setFormTerbuka(true)}>
                Ikut kirim
              </Tombol>
            </div>
          )}

          <FormIkutKirim
            slotId={detail.data.id}
            terbuka={formTerbuka}
            onTutup={() => setFormTerbuka(false)}
            onLuapan={setLuapanInfo}
          />
          <DialogLuapanKapasitas info={luapanInfo} onTutup={() => setLuapanInfo(null)} />
        </>
      )}
    </div>
  );
}
