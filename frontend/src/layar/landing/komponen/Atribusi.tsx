/** Hasil atribusi (masih dalam blok navy bersama #perjalanan) — menjelaskan
 *  "TIDAK TERBUKTI" sebagai salah satu dari 4 kemungkinan hasil atribusi mutu. */

import { useTampilSaatScroll } from "../useTampilSaatScroll";

export default function Atribusi() {
  const reveal = useTampilSaatScroll<HTMLDivElement>();

  return (
    <section className="lp-atribusi" aria-labelledby="atribusi-judul">
      <div ref={reveal.ref} className="lp-atribusi__inner">
        <h2 id="atribusi-judul" className={`lp-atribusi__eyebrow lp-reveal ${reveal.terlihat ? "is-visible" : ""}`}>
          Hasil atribusi · slot #CKJ-0042
        </h2>
        <p
          className={`lp-atribusi__hasil angka lp-reveal ${reveal.terlihat ? "is-visible" : ""}`}
          style={{ transitionDelay: reveal.terlihat ? "60ms" : "0ms" }}
        >
          TIDAK TERBUKTI
        </p>
        <p
          className={`lp-atribusi__desc lp-reveal ${reveal.terlihat ? "is-visible" : ""}`}
          style={{ transitionDelay: reveal.terlihat ? "120ms" : "0ms" }}
        >
          Mutu asal 4, mutu tiba 3. Waktu tempuh masih di bawah ambang, sisa umur simpan masih aman. Ada
          penurunan, tapi tidak ada bukti paparan berlebih. Sistem tidak menunjuk siapa pun.
        </p>
        <p
          className={`lp-atribusi__opsi lp-reveal ${reveal.terlihat ? "is-visible" : ""}`}
          style={{ transitionDelay: reveal.terlihat ? "180ms" : "0ms" }}
        >
          Empat kemungkinan hasil: <strong>PETANI</strong> (sudah turun sebelum berangkat),{" "}
          <strong>LOGISTIK</strong> (terjadi di perjalanan), <strong>NORMAL</strong> (tidak ada penurunan), dan{" "}
          <strong>TIDAK TERBUKTI</strong>. Yang terakhir sengaja ada — sistem yang selalu bisa menunjuk pihak
          bersalah sedang mengaku tahu hal yang tidak diketahuinya.
        </p>
      </div>
    </section>
  );
}
