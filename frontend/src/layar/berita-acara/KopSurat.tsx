/** Kop surat Berita Acara (§9.8) — kode slot, tanggal, titik kumpul, daftar tujuan.
 *  Judul dokumen terpusat (kop resmi), rincian di bawahnya sebagai daftar deskripsi. */

import type { components } from "@/api/client";
import { formatAngka, formatTanggal } from "@/utils/format";

type BeritaAcaraOut = components["schemas"]["BeritaAcaraOut"];
type RuteSegmenOut = components["schemas"]["RuteSegmenOut"];

interface KopSuratProps {
  data: BeritaAcaraOut;
}

export default function KopSurat({ data }: KopSuratProps) {
  const lokasiTitikKumpul = [
    data.titik_kumpul.desa && `Desa ${data.titik_kumpul.desa}`,
    data.titik_kumpul.kecamatan && `Kec. ${data.titik_kumpul.kecamatan}`,
    data.titik_kumpul.kabupaten && `Kab. ${data.titik_kumpul.kabupaten}`,
  ]
    .filter(Boolean)
    .join(", ");

  return (
    <header className="flex flex-col gap-4 border-b-2 border-tanah pb-4">
      <div className="text-center">
        <p className="text-subjudul font-bold uppercase tracking-wide text-tanah">Berita Acara Serah Terima</p>
        <p className="text-keterangan font-semibold uppercase tracking-widest text-tanah/60">Satu Muatan</p>
      </div>

      <dl className="grid grid-cols-[auto,1fr] gap-x-3 gap-y-1.5 text-base text-tanah">
        <dt className="text-keterangan font-medium text-tanah/60">Kode slot</dt>
        <dd className="angka font-semibold">{data.kode_slot}</dd>

        <dt className="text-keterangan font-medium text-tanah/60">Tanggal kirim</dt>
        <dd>{formatTanggal(data.tanggal_kirim)}</dd>

        <dt className="text-keterangan font-medium text-tanah/60">Titik Kumpul</dt>
        <dd>
          {data.titik_kumpul.nama}
          {lokasiTitikKumpul && <span className="text-tanah/70">, {lokasiTitikKumpul}</span>}
        </dd>

        <dt className="text-keterangan font-medium text-tanah/60">Tujuan</dt>
        <dd>
          <ol className="flex flex-col gap-0.5">
            {data.tujuan.map((t: RuteSegmenOut) => (
              <li key={t.penerima_id}>
                {t.urutan}. {t.nama_penerima}{" "}
                <span className="angka text-tanah/60">({formatAngka(t.jarak_segmen_km)} km)</span>
              </li>
            ))}
          </ol>
        </dd>
      </dl>
    </header>
  );
}
