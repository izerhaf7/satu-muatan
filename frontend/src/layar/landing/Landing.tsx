/** Landing publik (Fase 2.6) — placeholder Tahap 0; dibangun penuh oleh
 *  agent fase2-6/landing (hero three.js, angka band, cara kerja, fitur, CTA). */

import TombolTautan from "@/komponen/TombolTautan";

export default function Landing() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-6 px-5 text-center">
      <img src="/ikon-192.png" alt="Logo Satu Muatan" className="h-20 w-20" />
      <h1 className="text-display text-tanah">
        Satu muatan penuh. <span className="text-daun">Ongkos turun.</span>
      </h1>
      <p className="text-base text-tanah/70">
        Perkakas koperasi desa untuk mengirim panen bersama-sama — dengan harga atap terkunci dan
        bukti mutu di setiap serah terima.
      </p>
      <TombolTautan to="/masuk">Masuk</TombolTautan>
    </main>
  );
}
