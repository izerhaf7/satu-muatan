/** #demo — CTA penutup "Cek dulu, gratis." + Footer bersarang di blok navy yang
 *  sama (persis desain). CTA utama → /masuk (React Router, bukan anchor). */

import { Link } from "react-router-dom";

import { useTampilSaatScroll } from "../useTampilSaatScroll";
import Footer from "./Footer";

export default function CtaPenutup() {
  const reveal = useTampilSaatScroll<HTMLDivElement>();

  return (
    <section id="demo" className="lp-penutup" aria-labelledby="penutup-judul">
      <div ref={reveal.ref} className="lp-penutup__inner">
        <h2 id="penutup-judul" className={`lp-penutup__judul lp-reveal ${reveal.terlihat ? "is-visible" : ""}`}>
          Cek dulu, gratis.
        </h2>
        <p
          className={`lp-penutup__desc lp-reveal ${reveal.terlihat ? "is-visible" : ""}`}
          style={{ transitionDelay: reveal.terlihat ? "60ms" : "0ms" }}
        >
          Masukkan tujuan dan jumlah kilogram. Beberapa detik kemudian kamu tahu ongkos angkutnya berapa, dan
          bisa turun sampai berapa.
        </p>
        <div
          className={`lp-penutup__cta lp-reveal ${reveal.terlihat ? "is-visible" : ""}`}
          style={{ transitionDelay: reveal.terlihat ? "120ms" : "0ms" }}
        >
          <Link to="/masuk" className="lp-btn lp-btn--isi">
            Hitung ongkos kirimanku
          </Link>
        </div>

        <Footer />
      </div>
    </section>
  );
}
