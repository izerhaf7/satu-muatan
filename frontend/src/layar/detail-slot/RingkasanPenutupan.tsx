/** Ringkasan setelah slot tidak lagi DIBUKA (§5.4, §5.5) — dibaca beda per peran:
 *  Koperasi lihat subsidi + rincian tagihan/kembalian tiap peserta + tautan lanjutan
 *  (Muat/Lacak/Berita Acara). Petani lihat harga final & kembalian miliknya sendiri.
 *  Penerima lihat status pengiriman saja. Status BATAL tidak menampilkan apa pun
 *  di luar catatan pembatalan — tidak ada proses lanjutan untuk ditautkan. */

import { Link } from "react-router-dom";

import AngkaHarga from "@/komponen/AngkaHarga";
import type { components } from "@/api/client";
import { formatAngka, formatRupiah } from "@/utils/format";

type SlotDetailOut = components["schemas"]["SlotDetailOut"];
type PeranPengguna = components["schemas"]["PeranPengguna"];

interface RingkasanPenutupanProps {
  slot: SlotDetailOut;
  peran: PeranPengguna;
  penggunaId: string;
}

const kelasTautan =
  "flex min-h-sentuh flex-1 items-center justify-center rounded-md border-2 border-tanah px-3 text-center text-sm font-semibold text-tanah";

export default function RingkasanPenutupan({ slot, peran, penggunaId }: RingkasanPenutupanProps) {
  if (slot.status === "BATAL") {
    return (
      <section className="rounded-lg border-2 border-kabut p-4 text-center">
        <p className="text-base text-tanah/70">Slot ini dibatalkan. Tidak ada tagihan untuk peserta mana pun.</p>
      </section>
    );
  }

  return (
    <section aria-label="Ringkasan slot" className="flex flex-col gap-4 rounded-lg border-2 border-kabut p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-base font-semibold text-tanah">Harga final</p>
        <AngkaHarga nilai={slot.harga_final_per_kg ?? null} ukuran="sedang" satuan="/kg" />
      </div>

      {peran === "KOPERASI" && (
        <>
          {slot.subsidi_koperasi !== 0 && (
            <p className="text-sm text-tanah/80">
              {/* K11: negatif = surplus pembulatan ceil (masuk kas koperasi), bukan subsidi */}
              {slot.subsidi_koperasi > 0 ? "Selisih ditanggung koperasi:" : "Sisa pembulatan (masuk kas koperasi):"}{" "}
              <span className={`angka font-semibold ${slot.subsidi_koperasi > 0 ? "text-tanah-liat" : "text-tanah/70"}`}>
                {formatRupiah(Math.abs(slot.subsidi_koperasi))}
              </span>
            </p>
          )}

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b-2 border-kabut text-tanah/60">
                  <th className="py-2 pr-3 font-medium">Petani</th>
                  <th className="py-2 pr-3 font-medium">Volume</th>
                  <th className="py-2 pr-3 font-medium">Tagihan</th>
                  <th className="py-2 font-medium">Kembalian</th>
                </tr>
              </thead>
              <tbody>
                {slot.partisipasi.map((p) => {
                  const hargaFinal = p.harga_final_per_kg ?? 0;
                  const tagihan = p.volume_kg * hargaFinal;
                  return (
                    <tr key={p.id} className="border-b border-kabut/60">
                      <td className="py-2 pr-3">
                        <p className="text-tanah">{p.nama_petani}</p>
                        <p className="text-tanah/50">{p.nama_komoditas}</p>
                      </td>
                      <td className="angka py-2 pr-3">{formatAngka(p.volume_kg)} kg</td>
                      <td className="angka py-2 pr-3">{formatRupiah(tagihan)}</td>
                      <td className="angka py-2">
                        {p.kembalian_rp > 0 ? (
                          <span className="font-semibold text-daun">{formatRupiah(p.kembalian_rp)}</span>
                        ) : (
                          formatRupiah(p.kembalian_rp)
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap gap-2">
            <Link to={`/slot/${slot.id}/muat`} className={kelasTautan}>
              Muat
            </Link>
            <Link to={`/slot/${slot.id}/lacak`} className={kelasTautan}>
              Lacak
            </Link>
            <Link to={`/slot/${slot.id}/berita-acara`} className={kelasTautan}>
              Berita Acara
            </Link>
          </div>
        </>
      )}

      {peran === "PETANI" &&
        (() => {
          const sendiri = slot.partisipasi.find((p) => p.petani_id === penggunaId);
          if (!sendiri) return null;
          return (
            <>
              <div className="flex items-center justify-between gap-2 border-t-2 border-kabut pt-3">
                <p className="text-base text-tanah/80">Kembalian kamu</p>
                <p className="angka text-lg font-bold text-daun">{formatRupiah(sendiri.kembalian_rp)}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Link to={`/slot/${slot.id}/lacak`} className={kelasTautan}>
                  Lacak
                </Link>
                <Link to={`/slot/${slot.id}/berita-acara`} className={kelasTautan}>
                  Berita Acara
                </Link>
              </div>
            </>
          );
        })()}

      {peran === "PENERIMA" && (
        <div className="flex flex-wrap gap-2">
          <Link to={`/slot/${slot.id}/lacak`} className={kelasTautan}>
            Lacak
          </Link>
        </div>
      )}
    </section>
  );
}
