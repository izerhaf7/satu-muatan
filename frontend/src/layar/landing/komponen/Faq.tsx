/** #faq — accordion 6 pertanyaan, satu terbuka dalam satu waktu (setupFaq desain
 *  asli), diterjemahkan ke useState<number|null> + teknik CSS grid-template-rows
 *  0fr→1fr (tanpa perlu ukur offsetHeight manual). */

import { useState } from "react";

import { useTampilSaatScroll } from "../useTampilSaatScroll";

interface Butir {
  q: string;
  a: string;
}

const BUTIR: Butir[] = [
  {
    q: "Harus punya koperasi atau kelompok tani?",
    a: "Tidak. Titik kumpul bisa rumah atau lahan siapa saja yang disepakati bersama.",
  },
  {
    q: "Harus ganti pembeli?",
    a: "Tidak. Pembelimu tetap sama. Kami hanya mengurus pengangkutannya, bukan jual-belinya.",
  },
  {
    q: "Kalau tidak ada yang gabung?",
    a: "Kamu bayar harga atap yang sudah dikunci saat daftar. Tidak pernah lebih dari itu.",
  },
  {
    q: "Harus menunggu berapa lama?",
    a: "Kamu yang menentukan tanggal siap. Sistem menggabungkan kiriman dalam rentang beberapa hari di sekitarnya.",
  },
  {
    q: "Siapa yang menimbang dan menilai mutunya?",
    a: "Pengemudi yang menimbang, memfoto, dan mengisi nilai mutunya. Kamu tinggal setuju atau keberatan.",
  },
  {
    q: "Cocok untuk komoditas apa?",
    a: "Sayur curah bervolume besar dengan harga sedang — kubis, sawi, tomat, wortel. Untuk komoditas bernilai sangat tinggi seperti cabai, ongkos angkutnya kecil dibanding nilainya, jadi penghematannya tidak terasa.",
  },
];

export default function Faq() {
  const [terbuka, setTerbuka] = useState<number | null>(0);
  const headReveal = useTampilSaatScroll<HTMLDivElement>();
  const listReveal = useTampilSaatScroll<HTMLDivElement>();

  return (
    <section id="faq" className="lp-faq" aria-labelledby="faq-judul">
      <div className="lp-faq__inner">
        <div ref={headReveal.ref} className={`lp-reveal ${headReveal.terlihat ? "is-visible" : ""}`}>
          <h2 id="faq-judul" className="lp-faq__eyebrow">
            FAQ
          </h2>
          <p className="lp-faq__judul">Pertanyaan yang sering muncul.</p>
        </div>

        <div ref={listReveal.ref} className="lp-faq__list">
          {BUTIR.map((butir, i) => {
            const terbukaIni = terbuka === i;
            return (
              <div
                key={butir.q}
                className={`lp-faq__item ${terbukaIni ? "lp-faq__item--open" : ""} lp-reveal ${listReveal.terlihat ? "is-visible" : ""}`}
                style={{ transitionDelay: listReveal.terlihat ? `${i * 40}ms` : "0ms" }}
              >
                <button
                  type="button"
                  className="lp-faq__btn"
                  aria-expanded={terbukaIni}
                  onClick={() => setTerbuka(terbukaIni ? null : i)}
                >
                  <span>{butir.q}</span>
                  <span aria-hidden="true" className="lp-faq__icon">
                    <span className="lp-faq__icon-h" />
                    <span className="lp-faq__icon-v" />
                  </span>
                </button>
                <div className="lp-faq__panel">
                  <div className="lp-faq__panel-inner">
                    <p>{butir.a}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
