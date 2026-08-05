/** #cara-kerja — lima langkah proses, angka besar sticky di kiri (desktop),
 *  termasuk contoh harga turun (Rp1.300 → Rp426) dan angka dampak (252 truk-km,
 *  63 kg CO2e). Target smooth-scroll dari CTA sekunder hero & nav. */

import { useTampilSaatScroll } from "../useTampilSaatScroll";

export default function CaraKerja() {
  const headReveal = useTampilSaatScroll<HTMLDivElement>();
  const listReveal = useTampilSaatScroll<HTMLOListElement>();
  const penutupReveal = useTampilSaatScroll<HTMLParagraphElement>();

  return (
    <section id="cara-kerja" className="lp-cara scroll-mt-16" aria-labelledby="cara-judul">
      <div className="lp-cara__inner">
        <div ref={headReveal.ref} className={`lp-reveal ${headReveal.terlihat ? "is-visible" : ""}`}>
          <h2 id="cara-judul" className="lp-cara__eyebrow">
            Cara kerja
          </h2>
          <p className="lp-cara__judul">Bagaimana Satu Muatan menyelesaikan ketiganya</p>
          <p className="lp-cara__lead">Satu mekanisme, tiga hasil sekaligus.</p>
        </div>

        <ol ref={listReveal.ref} className="lp-cara__list">
          <li className="lp-cara__item">
            <div className="lp-cara__nomor angka">01</div>
            <div className={`lp-reveal ${listReveal.terlihat ? "is-visible" : ""}`}>
              <h3 className="lp-cara__item-judul">Daftarkan kiriman</h3>
              <p className="lp-cara__item-desc">
                Isi tujuan, jumlah kilogram, tanggal siap. Muncul dua angka: harga maksimal yang kamu kunci, dan
                perkiraan kalau ada yang gabung.
              </p>
            </div>
          </li>
          <li className="lp-cara__item">
            <div className="lp-cara__nomor angka">02</div>
            <div
              className={`lp-reveal ${listReveal.terlihat ? "is-visible" : ""}`}
              style={{ transitionDelay: listReveal.terlihat ? "60ms" : "0ms" }}
            >
              <h3 className="lp-cara__item-judul">Sistem mencocokkan otomatis</h3>
              <p className="lp-cara__item-desc">
                Kiriman lain yang searah dan tanggalnya berdekatan digabungkan jadi satu muatan. Kamu tidak perlu
                kenal siapa pun.
              </p>
            </div>
          </li>
          <li className="lp-cara__item">
            <div className="lp-cara__nomor angka">03</div>
            <div
              className={`lp-reveal ${listReveal.terlihat ? "is-visible" : ""}`}
              style={{ transitionDelay: listReveal.terlihat ? "120ms" : "0ms" }}
            >
              <h3 className="lp-cara__item-judul">Harga turun sendiri</h3>
              <p className="lp-cara__item-desc">
                Tiap ada peserta baru, harga semua orang ikut turun — termasuk yang daftar duluan. Kelebihan
                bayarmu dikembalikan.
              </p>
              <p className="lp-cara__harga">
                <span className="lp-cara__harga-lama angka">Rp1.300</span>
                <span aria-hidden="true">→</span>
                <span className="lp-cara__harga-baru angka">Rp426</span>
                <span className="lp-cara__harga-unit">per kg</span>
              </p>
            </div>
          </li>
          <li className="lp-cara__item">
            <div className="lp-cara__nomor angka">04</div>
            <div
              className={`lp-reveal ${listReveal.terlihat ? "is-visible" : ""}`}
              style={{ transitionDelay: listReveal.terlihat ? "180ms" : "0ms" }}
            >
              <h3 className="lp-cara__item-judul">Empat perjalanan jadi satu</h3>
              <p className="lp-cara__item-desc">
                Di sinilah emisinya berkurang. Bukan karena truknya lebih ramah lingkungan, tapi karena tiga
                perjalanan tidak jadi ditempuh.
              </p>
              <div className="lp-cara__dampak">
                <p className="lp-cara__dampak-item angka">
                  252 truk-km <span>hilang</span>
                </p>
                <p className="lp-cara__dampak-item angka">
                  63 kg CO₂e <span>tidak jadi keluar</span>
                </p>
              </div>
            </div>
          </li>
          <li className="lp-cara__item">
            <div className="lp-cara__nomor angka">05</div>
            <div
              className={`lp-reveal ${listReveal.terlihat ? "is-visible" : ""}`}
              style={{ transitionDelay: listReveal.terlihat ? "240ms" : "0ms" }}
            >
              <h3 className="lp-cara__item-judul">Perjalanan tercatat, mutu terlacak</h3>
              <p className="lp-cara__item-desc">
                Suhu, posisi, dan lama perjalanan direkam. Sampai tujuan terbit Berita Acara digital — dan sistem
                bisa menunjukkan penurunan mutu terjadi sebelum berangkat atau selama di jalan.
              </p>
            </div>
          </li>
        </ol>

        <p ref={penutupReveal.ref} className={`lp-cara__penutup lp-reveal ${penutupReveal.terlihat ? "is-visible" : ""}`}>
          Satu perubahan — truk yang berangkat penuh — menyelesaikan ketiganya. Ongkos turun karena kilogramnya
          lebih banyak menanggung tarif yang sama. Emisi turun karena perjalanannya lebih sedikit. Mutu terjaga
          karena perjalanannya sekarang punya catatan.
        </p>
      </div>
    </section>
  );
}
