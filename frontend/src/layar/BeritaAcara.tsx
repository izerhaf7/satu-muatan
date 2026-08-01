/** Berita Acara Serah Terima (§9.8) — halaman siap cetak (`window.print()`, K4).
 *  Layar tetap mobile-friendly; `berita-acara/cetak.css` mengubahnya jadi dokumen
 *  A4 hitam-di-atas-putih saat dicetak. TANPA library PDF (spec §9.8). */

import { Printer } from "lucide-react";
import { useParams } from "react-router-dom";

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { SkeletonKartu } from "@/komponen/Skeleton";
import Tombol from "@/komponen/Tombol";
import { useBeritaAcara } from "@/hooks/useBeritaAcara";

import "./berita-acara/cetak.css";

import KopSurat from "./berita-acara/KopSurat";
import RincianOngkos from "./berita-acara/RincianOngkos";
import TabelLot from "./berita-acara/TabelLot";
import TandaTangan from "./berita-acara/TandaTangan";

export default function BeritaAcara() {
  const { id } = useParams();
  const beritaAcara = useBeritaAcara(id);

  return (
    <div className="berita-acara flex flex-col gap-6 lg:mx-auto lg:max-w-3xl">
      <div className="no-print">
        <HeaderLayar
          judul="Berita Acara"
          kembaliKe={id ? `/slot/${id}` : "/beranda"}
          aksi={
            beritaAcara.data && (
              <Tombol onClick={() => window.print()} ikon={Printer} className="px-4 text-keterangan">
                Cetak / Simpan PDF
              </Tombol>
            )
          }
        />
      </div>

      {beritaAcara.isLoading && (
        <div className="no-print">
          <SkeletonKartu jumlah={3} />
        </div>
      )}

      {beritaAcara.isError && (
        <div className="no-print">
          <KartuGalat pesan="Gagal memuat berita acara." onCobaLagi={() => beritaAcara.refetch()} />
        </div>
      )}

      {beritaAcara.data && (
        <div className="dokumen-ba kartu-tonjol flex flex-col gap-6 p-5">
          <KopSurat data={beritaAcara.data} />
          {beritaAcara.data.lot.length === 0 ? (
            <KeadaanKosong pesan="Slot ini belum punya lot untuk diserahterimakan." />
          ) : (
            <TabelLot lot={beritaAcara.data.lot} />
          )}
          <RincianOngkos
            rincian={beritaAcara.data.rincian_ongkos}
            biayaTotal={beritaAcara.data.biaya_total ?? null}
            hargaFinalPerKg={beritaAcara.data.harga_final_per_kg ?? null}
            subsidiKoperasi={beritaAcara.data.subsidi_koperasi}
          />
          <TandaTangan />
        </div>
      )}
    </div>
  );
}
