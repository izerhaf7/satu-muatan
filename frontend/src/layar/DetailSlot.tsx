/** Layar "Muatanmu" / Detail Slot (§9.4) — LAYAR UTAMA DEMO. Harga berjalan
 *  turun hidup-hidup di sebelah harga atap yang diam terkunci; juri paham
 *  seluruh produk dalam hitungan detik tanpa penjelasan. Dipoll 3 detik.
 *
 *  K13: layar ini murni PEMANTAUAN. Tidak ada lagi tombol "Ikut kirim" —
 *  petani masuk ke sebuah muatan lewat Kirim Panen, bukan dengan memilih. */

import { useParams } from "react-router-dom";

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import RingkasanResi from "@/komponen/RingkasanResi";
import { SkeletonAngka, SkeletonKartu } from "@/komponen/Skeleton";
import { useDetailSlot } from "@/hooks/useDetailSlot";
import { useAuthStore } from "@/stores/authStore";

import DaftarPeserta from "./detail-slot/DaftarPeserta";
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

  return (
    <div className="flex flex-col gap-6 lg:grid lg:grid-cols-2 lg:items-start">
      <div className="lg:col-span-2">
        {detail.data ? (
          <HeaderDetailSlot slot={detail.data} />
        ) : (
          <HeaderLayar judul="Detail slot" kembaliKe="/beranda" />
        )}
      </div>

      {detail.isLoading && (
        <div className="flex flex-col gap-6 lg:col-span-2">
          <SkeletonAngka className="kartu-hero" />
          <SkeletonKartu jumlah={4} />
        </div>
      )}

      {detail.isError && (
        <div className="lg:col-span-2">
          <KartuGalat pesan="Gagal memuat detail slot." onCobaLagi={() => detail.refetch()} />
        </div>
      )}

      {detail.data && (
        <>
          <div className="flex flex-col gap-6">
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
          </div>

          <div className="flex flex-col gap-6">
            <section aria-label="Peserta" className="flex flex-col gap-2">
              <h2 className="text-subjudul text-tanah">Peserta</h2>
              <DaftarPeserta partisipasi={detail.data.partisipasi} />
            </section>

            <RingkasanResi resi={detail.data.resi} />

            {detail.data.status !== "DIBUKA" && pengguna && (
              <RingkasanPenutupan slot={detail.data} peran={pengguna.peran} penggunaId={pengguna.id} />
            )}

            {pengguna?.peran === "PETUGAS" && detail.data.status === "DIBUKA" && (
              <PanelTutupSlot slotId={detail.data.id} />
            )}
          </div>

          {/* K13: tombol "Ikut kirim" DIHAPUS. Petani tidak memilih muatan —
              dia mengirim panen lewat layar Kirim Panen dan sistem yang
              mencocokkan. Layar ini murni untuk memantau harga & progres. */}
        </>
      )}
    </div>
  );
}
