/** Layar Detail Slot (§9.4) — LAYAR UTAMA DEMO. Harga berjalan turun hidup-hidup
 *  di sebelah harga atap yang diam terkunci; juri paham seluruh produk dalam
 *  hitungan detik tanpa penjelasan. Dipoll 3 detik (useDetailSlot). */

import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import KeadaanKosong from "@/komponen/KeadaanKosong";
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
      <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6">
        <KeadaanKosong pesan="Slot tidak ditemukan." teksAksi="Kembali ke Beranda" ke="/" />
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6 pb-28">
      <Link to="/" className="text-sm font-medium text-tanah/60">
        ← Beranda
      </Link>

      {detail.isLoading && <p className="text-base text-tanah/60">Memuat detail slot…</p>}

      {detail.isError && (
        <div className="flex flex-col items-start gap-3 rounded-lg border-2 border-tanah-liat/40 p-4">
          <p className="text-base text-tanah-liat">Gagal memuat detail slot.</p>
          <Tombol varian="sekunder" onClick={() => detail.refetch()}>
            Coba lagi
          </Tombol>
        </div>
      )}

      {detail.data && (
        <>
          <HeaderDetailSlot slot={detail.data} />

          {detail.data.status === "DIBUKA" && <HargaBerjalanHero hargaPerKg={detail.data.harga_berjalan_per_kg ?? null} />}

          {pengguna?.peran === "PETANI" && detail.data.status === "DIBUKA" && detail.data.atap_saya_per_kg !== null && (
            <KartuAtapSaya
              atapPerKg={detail.data.atap_saya_per_kg!}
              hematPerKg={detail.data.hemat_saya_per_kg ?? null}
              volumeSayaKg={detail.data.partisipasi
                .filter((p) => p.petani_id === pengguna.id)
                .reduce((total, p) => total + p.volume_kg, 0)}
            />
          )}

          <KapasitasTierBar
            volumeKg={detail.data.volume_total_kg}
            rencana={detail.data.rencana_saat_ini}
            jumlahPeserta={detail.data.partisipasi.length}
          />

          <section aria-label="Peserta" className="flex flex-col gap-2">
            <h2 className="text-base font-semibold text-tanah">Peserta</h2>
            <DaftarPeserta partisipasi={detail.data.partisipasi} />
          </section>

          {detail.data.status !== "DIBUKA" && pengguna && (
            <RingkasanPenutupan slot={detail.data} peran={pengguna.peran} penggunaId={pengguna.id} />
          )}

          {pengguna?.peran === "KOPERASI" && detail.data.status === "DIBUKA" && (
            <PanelTutupSlot slotId={detail.data.id} />
          )}

          {pengguna?.peran === "PETANI" && detail.data.status === "DIBUKA" && detail.data.atap_saya_per_kg === null && (
            <div className="fixed inset-x-0 bottom-0 mx-auto max-w-md border-t-2 border-kabut bg-kertas p-4">
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
    </main>
  );
}
