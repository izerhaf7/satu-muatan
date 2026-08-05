/** #masalah — tiga kerugian akibat truk berangkat setengah kosong (band navy). */

import { useTampilSaatScroll } from "../useTampilSaatScroll";

interface Item {
  label: string;
  judul: string;
  desc: string;
  angka: string;
  keterangan: string;
  netral?: boolean;
}

const ITEM: Item[] = [
  {
    label: "01 · ONGKOS",
    judul: "Ongkos angkut tidak masuk akal untuk panen kecil.",
    desc: "Truk dijual per perjalanan, bukan per kilogram. Panen 300 kg tetap membayar satu truk penuh. Di tingkat petani, transportasi menyedot 84,62% dari seluruh biaya logistik.",
    angka: "84,62%",
    keterangan: "biaya logistik",
  },
  {
    label: "02 · EMISI",
    judul: "Emisi yang seharusnya tidak perlu ada.",
    desc: "Empat petani, empat truk, satu koridor yang sama. Tiga perjalanan di antaranya sebenarnya tidak perlu terjadi — beserta seluruh emisi yang menyertainya.",
    angka: "3 dari 4",
    keterangan: "perjalanan mubazir",
    netral: true,
  },
  {
    label: "03 · BUKTI",
    judul: "Tidak ada yang tahu apa yang terjadi di jalan.",
    desc: "Berapa suhu di dalam bak, berapa lama menunggu, berapa lama perjalanannya. Saat sayur tiba layu, tidak ada bukti apa pun. Sengketa diputus oleh siapa yang posisinya lebih kuat.",
    angka: "0 bukti",
    keterangan: "saat sengketa",
    netral: true,
  },
];

export default function Masalah() {
  const judulReveal = useTampilSaatScroll<HTMLParagraphElement>();
  const listReveal = useTampilSaatScroll<HTMLOListElement>();

  return (
    <section id="masalah" className="lp-masalah" aria-labelledby="masalah-judul">
      <div className="lp-masalah__inner">
        <h2 id="masalah-judul" className="lp-masalah__eyebrow">
          Tiga masalah
        </h2>
        <p
          ref={judulReveal.ref}
          className={`lp-masalah__judul lp-reveal ${judulReveal.terlihat ? "is-visible" : ""}`}
        >
          Satu perjalanan setengah kosong menimbulkan tiga kerugian sekaligus.
        </p>

        <ol ref={listReveal.ref} className="lp-masalah__list">
          {ITEM.map((item, i) => (
            <li
              key={item.label}
              className={`lp-masalah__item lp-reveal ${listReveal.terlihat ? "is-visible" : ""}`}
              style={{ transitionDelay: listReveal.terlihat ? `${i * 80}ms` : "0ms" }}
            >
              <span className="lp-masalah__label">{item.label}</span>
              <p className="lp-masalah__judul-item">{item.judul}</p>
              <p className="lp-masalah__desc">{item.desc}</p>
              <p className={`lp-masalah__angka angka ${item.netral ? "lp-masalah__angka--netral" : ""}`}>
                {item.angka} <span>{item.keterangan}</span>
              </p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
