/** Batas galat (React error boundary) — K14.
 *
 *  Sebelum ini TIDAK ADA satu pun error boundary di aplikasi, padahal empat
 *  layar berat di-`lazy()`. Akibatnya satu throw saat render — atau satu chunk
 *  basi setelah service worker memperbarui dirinya — memutus seluruh pohon React
 *  dan menyisakan LAYAR PUTIH tanpa petunjuk apa pun. Itulah bentuk kegagalan
 *  yang dilaporkan di layar Lacak.
 *
 *  Komponen ini tidak menyembunyikan galat: ia menampilkannya, memberi jalan
 *  keluar, dan tetap mencatatnya ke konsol supaya bisa ditelusuri. */

import { Component, type ErrorInfo, type ReactNode } from "react";
import { RefreshCw, TriangleAlert } from "lucide-react";

interface BatasGalatProps {
  children: ReactNode;
}

interface BatasGalatState {
  galat: Error | null;
}

export default class BatasGalat extends Component<BatasGalatProps, BatasGalatState> {
  state: BatasGalatState = { galat: null };

  static getDerivedStateFromError(galat: Error): BatasGalatState {
    return { galat };
  }

  componentDidCatch(galat: Error, info: ErrorInfo) {
    // Sengaja tetap di konsol — ini satu-satunya jejak saat juri/penguji
    // melaporkan "layarnya kosong".
    console.error("Layar gagal dirender:", galat, info.componentStack);
  }

  render() {
    const { galat } = this.state;
    if (!galat) return this.props.children;

    return (
      <div className="mx-auto flex max-w-md flex-col gap-4 px-5 py-10">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-tanah-liat/10 text-tanah-liat">
          <TriangleAlert aria-hidden className="h-6 w-6" strokeWidth={2.25} />
        </span>
        <div className="flex flex-col gap-1">
          <h1 className="text-judul text-tanah">Layar ini gagal ditampilkan</h1>
          <p className="text-base text-tanah/70">
            Bukan datamu yang hilang — hanya tampilannya yang berhenti. Muat ulang biasanya cukup.
          </p>
        </div>

        <p className="rounded-lg bg-kabut/40 px-3 py-2 text-keterangan text-tanah/70">{galat.message}</p>

        <button
          type="button"
          onClick={() => window.location.reload()}
          className="inline-flex min-h-sentuh items-center justify-center gap-2 rounded-lg bg-daun px-4 text-base font-semibold text-kertas transition-colors duration-cepat hover:bg-daun/90"
        >
          <RefreshCw aria-hidden className="h-4 w-4" />
          Muat ulang
        </button>
      </div>
    );
  }
}
