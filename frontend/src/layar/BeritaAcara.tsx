/** Berita Acara Serah Terima (§9.8) — halaman siap cetak (`window.print()`, K4).
 *  Layar tetap mobile-friendly; `berita-acara/cetak.css` mengubahnya jadi dokumen
 *  A4 hitam-di-atas-putih saat dicetak. TANPA library PDF (spec §9.8). */

import { Link, useParams } from "react-router-dom";

import KeadaanKosong from "@/komponen/KeadaanKosong";
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
    <main className="berita-acara mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6">
      <div className="no-print flex items-center justify-between gap-3">
        <BackLink id={id} />
        {beritaAcara.data && (
          <Tombol onClick={() => window.print()} className="px-4 text-sm">
            Cetak / Simpan PDF
          </Tombol>
        )}
      </div>

      {beritaAcara.isLoading && <p className="no-print text-base text-tanah/60">Memuat berita acara…</p>}

      {beritaAcara.isError && (
        <div className="no-print flex flex-col items-start gap-3 rounded-lg border-2 border-tanah-liat/40 p-4">
          <p className="text-base text-tanah-liat">Gagal memuat berita acara.</p>
          <Tombol varian="sekunder" onClick={() => beritaAcara.refetch()}>
            Coba lagi
          </Tombol>
        </div>
      )}

      {beritaAcara.data && (
        <>
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
        </>
      )}
    </main>
  );
}

function BackLink({ id }: { id: string | undefined }) {
  return (
    <Link
      to={id ? `/slot/${id}` : "/"}
      className="flex min-h-sentuh items-center text-base font-medium text-tanah underline underline-offset-2"
    >
      ← Kembali ke slot
    </Link>
  );
}
