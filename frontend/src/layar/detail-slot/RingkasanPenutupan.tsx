/** Ringkasan setelah slot tidak lagi DIBUKA (§5.4, §5.5) — dibaca beda per peran:
 *  Petugas lihat selisih + rincian tagihan/kembalian tiap peserta + tautan lanjutan
 *  (Muat/Lacak/Berita Acara). Petani lihat harga final & kembalian miliknya sendiri.
 *  Penerima lihat status pengiriman saja. Status BATAL tidak menampilkan apa pun
 *  di luar catatan pembatalan — tidak ada proses lanjutan untuk ditautkan.
 *  Logika (K11 subsidi negatif = surplus pembulatan) TIDAK diubah — hanya primitif
 *  tampilan (Tabel/Thead/Th/Td, TombolTautan). */

import AngkaHarga from "@/komponen/AngkaHarga";
import { Tabel, Td, Th, Thead } from "@/komponen/Tabel";
import TombolTautan from "@/komponen/TombolTautan";
import type { components } from "@/api/client";
import { formatAngka, formatRupiah } from "@/utils/format";

type SlotDetailOut = components["schemas"]["SlotDetailOut"];
type PeranPengguna = components["schemas"]["PeranPengguna"];
type PartisipasiOut = components["schemas"]["PartisipasiOut"];

interface RingkasanPenutupanProps {
  slot: SlotDetailOut;
  peran: PeranPengguna;
  penggunaId: string;
}

export default function RingkasanPenutupan({ slot, peran, penggunaId }: RingkasanPenutupanProps) {
  if (slot.status === "BATAL") {
    return (
      <section className="kartu-tonjol p-4 text-center">
        <p className="text-base text-tanah/70">Slot ini dibatalkan. Tidak ada tagihan untuk peserta mana pun.</p>
      </section>
    );
  }

  return (
    <section aria-label="Ringkasan slot" className="kartu-tonjol flex flex-col gap-4 p-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-subjudul text-tanah">Harga final</p>
        <AngkaHarga nilai={slot.harga_final_per_kg ?? null} ukuran="sedang" satuan="/kg" />
      </div>

      {peran === "PETUGAS" && (
        <>
          {slot.selisih_jaminan_atap !== 0 && (
            <p className="text-base text-tanah/80">
              {/* K11: negatif = surplus pembulatan ceil (masuk kas titik kumpul), bukan subsidi */}
              {slot.selisih_jaminan_atap > 0 ? "Selisih dijamin platform:" : "Sisa pembulatan (masuk kas titik kumpul):"}{" "}
              <span className={`angka font-semibold ${slot.selisih_jaminan_atap > 0 ? "text-tanah-liat" : "text-tanah/70"}`}>
                {formatRupiah(Math.abs(slot.selisih_jaminan_atap))}
              </span>
            </p>
          )}

          <Tabel>
            <Thead>
              <tr>
                <Th>Petani</Th>
                <Th>Volume</Th>
                <Th>Tagihan</Th>
                <Th>Kembalian</Th>
              </tr>
            </Thead>
            <tbody>
              {slot.partisipasi.map((p: PartisipasiOut) => {
                const hargaFinal = p.harga_final_per_kg ?? 0;
                const tagihan = p.volume_kg * hargaFinal;
                return (
                  <tr key={p.id}>
                    <Td>
                      <p className="text-tanah">{p.nama_petani}</p>
                      <p className="text-keterangan text-tanah/50">{p.nama_komoditas}</p>
                    </Td>
                    <Td className="angka">{formatAngka(p.volume_kg)} kg</Td>
                    <Td className="angka">{formatRupiah(tagihan)}</Td>
                    <Td className="angka">
                      {p.kembalian_rp > 0 ? (
                        <span className="font-semibold text-daun">{formatRupiah(p.kembalian_rp)}</span>
                      ) : (
                        formatRupiah(p.kembalian_rp)
                      )}
                    </Td>
                  </tr>
                );
              })}
            </tbody>
          </Tabel>

          <div className="flex flex-wrap gap-2">
            <TombolTautan to={`/slot/${slot.id}/muat`} varian="sekunder" className="flex-1">
              Muat
            </TombolTautan>
            {(slot.status === "JALAN" || slot.status === "SELESAI") && (
              <TombolTautan to={`/slot/${slot.id}/lacak`} varian="sekunder" className="flex-1">
                Lacak
              </TombolTautan>
            )}
            <TombolTautan to={`/slot/${slot.id}/berita-acara`} varian="sekunder" className="flex-1">
              Berita Acara
            </TombolTautan>
          </div>
        </>
      )}

      {peran === "PETANI" &&
        (() => {
          const sendiri = slot.partisipasi.find((p: PartisipasiOut) => p.petani_id === penggunaId);
          if (!sendiri) return null;
          return (
            <>
              <div className="flex items-center justify-between gap-2 rounded-lg bg-daun/10 px-3 py-2.5">
                <p className="text-base font-medium text-tanah">Kembalian kamu</p>
                <p className="angka text-lg font-bold text-daun">{formatRupiah(sendiri.kembalian_rp)}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <TombolTautan to={`/slot/${slot.id}/lacak`} varian="sekunder" className="flex-1">
                  Lacak
                </TombolTautan>
                <TombolTautan to={`/slot/${slot.id}/berita-acara`} varian="sekunder" className="flex-1">
                  Berita Acara
                </TombolTautan>
              </div>
            </>
          );
        })()}

      {peran === "PENERIMA" && (
        <div className="flex flex-wrap gap-2">
          <TombolTautan to={`/slot/${slot.id}/lacak`} varian="sekunder" className="flex-1">
            Lacak
          </TombolTautan>
        </div>
      )}
    </section>
  );
}
