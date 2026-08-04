/** Form alamat terstruktur (K14) — dipakai DUA kali: alamat penjemputan dan
 *  alamat tujuan.
 *
 *  Mengikuti standar penulisan alamat ekspedisi Indonesia: nama & nomor telepon
 *  yang bisa dihubungi, nama jalan + nomor, RT/RW, desa/kelurahan, kecamatan,
 *  kabupaten/kota, provinsi, kode pos, dan patokan. Surat jalan pun
 *  mensyaratkan data pengirim & penerima yang lengkap — satu baris teks bebas
 *  tidak cukup untuk logistik sungguhan.
 *
 *  Tiga cara mengisi, bebas dipilih pengguna:
 *  1. geser pin di peta  → alamat terisi otomatis (reverse geocoding);
 *  2. ketik nama daerah  → komponen wilayah terisi, peta melompat;
 *  3. ketik sendiri      → selalu bisa, karena data wilayah tidak selalu cocok
 *     dengan kenyataan di lapangan.
 *
 *  Rincian dilipat secara bawaan supaya petani yang sedang di kebun tidak
 *  dihadang formulir panjang; ringkasannya tetap tampak. */

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

import InputTeks from "@/komponen/InputTeks";
import PilihWilayah from "@/komponen/PilihWilayah";
import type { components } from "@/api/client";

type AlamatIn = components["schemas"]["AlamatIn"];
type GeokodeOut = components["schemas"]["GeokodeOut"];
type WilayahOut = components["schemas"]["WilayahOut"];

export type NilaiAlamat = AlamatIn;

export const ALAMAT_KOSONG: NilaiAlamat = {
  alamat: "",
  nama: null,
  telepon: null,
  jalan: null,
  rt_rw: null,
  desa: null,
  kecamatan: null,
  kabupaten: null,
  provinsi: null,
  kode_pos: null,
  patokan: null,
};

/** Rakit ringkasan satu baris dari komponen — inilah yang tampil di kartu,
 *  buku alamat, dan surat jalan. */
export function ringkasAlamat(a: NilaiAlamat): string {
  const bagian = [a.jalan, a.rt_rw ? `RT/RW ${a.rt_rw}` : null, a.desa, a.kecamatan, a.kabupaten, a.kode_pos]
    .map((b) => b?.trim())
    .filter((b): b is string => Boolean(b));
  return bagian.length > 0 ? bagian.join(", ") : a.alamat.trim();
}

/** Terapkan hasil reverse geocoding tanpa menimpa apa yang sudah diketik
 *  pengguna — pin adalah bantuan, bukan atasan. */
export function terapkanGeokode(a: NilaiAlamat, g: GeokodeOut): NilaiAlamat {
  return {
    ...a,
    desa: a.desa || g.desa || null,
    kecamatan: a.kecamatan || g.kecamatan || null,
    kabupaten: a.kabupaten || g.kabupaten || null,
    provinsi: a.provinsi || g.provinsi || null,
    kode_pos: a.kode_pos || g.kode_pos || null,
    alamat: a.alamat || g.alamat,
  };
}

/** Wilayah yang dipilih mengisi komponen dari jalurnya, dari yang paling
 *  spesifik ke yang paling umum. */
export function terapkanWilayah(a: NilaiAlamat, w: WilayahOut): NilaiAlamat {
  const bagian = w.jalur.split(",").map((b) => b.trim());
  const dasar: NilaiAlamat = { ...a, kode_pos: w.kode_pos ?? a.kode_pos };

  if (w.tingkat === "DESA") {
    return { ...dasar, desa: bagian[0] ?? null, kecamatan: bagian[1] ?? null, kabupaten: bagian[2] ?? null, provinsi: bagian[3] ?? null };
  }
  if (w.tingkat === "KECAMATAN") {
    return { ...dasar, kecamatan: bagian[0] ?? null, kabupaten: bagian[1] ?? null, provinsi: bagian[2] ?? null };
  }
  return { ...dasar, kabupaten: bagian[0] ?? null, provinsi: bagian[1] ?? null };
}

interface FormAlamatProps {
  judul: string;
  /** Prefix id supaya dua form di satu halaman tidak bertabrakan labelnya. */
  idPrefix: string;
  nilai: NilaiAlamat;
  onUbah: (a: NilaiAlamat) => void;
  labelNama: string;
  labelTelepon: string;
  /** Dipanggil saat pengguna memilih daerah yang punya koordinat. */
  onWilayahBerkoordinat?: (titik: { lat: number; lng: number }) => void;
  /** Ditampilkan di bawah judul — mis. status pembacaan alamat dari peta. */
  keterangan?: string;
}

export default function FormAlamat({
  judul,
  idPrefix,
  nilai,
  onUbah,
  labelNama,
  labelTelepon,
  onWilayahBerkoordinat,
  keterangan,
}: FormAlamatProps) {
  const [rincianTerbuka, setRincianTerbuka] = useState(false);

  function ubah(bagian: Partial<NilaiAlamat>) {
    onUbah({ ...nilai, ...bagian });
  }

  const jalurWilayah = [nilai.desa, nilai.kecamatan, nilai.kabupaten, nilai.provinsi]
    .filter(Boolean)
    .join(", ");

  return (
    <section aria-label={judul} className="flex flex-col gap-3">
      <div className="flex flex-col gap-0.5">
        <h3 className="text-subjudul text-tanah">{judul}</h3>
        {keterangan && <p className="text-keterangan text-tanah/55">{keterangan}</p>}
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <InputTeks
          label={labelNama}
          id={`${idPrefix}-nama`}
          value={nilai.nama ?? ""}
          onChange={(e) => ubah({ nama: e.target.value || null })}
          placeholder="Nama lengkap"
        />
        <InputTeks
          label={labelTelepon}
          id={`${idPrefix}-telepon`}
          type="tel"
          inputMode="tel"
          value={nilai.telepon ?? ""}
          onChange={(e) => ubah({ telepon: e.target.value || null })}
          placeholder="08xxxxxxxxxx"
        />
      </div>

      <PilihWilayah
        label="Desa / kecamatan"
        id={`${idPrefix}-wilayah`}
        nilai={jalurWilayah}
        onPilih={(w) => {
          onUbah(terapkanWilayah(nilai, w));
          if (w.lat != null && w.lng != null) onWilayahBerkoordinat?.({ lat: w.lat, lng: w.lng });
        }}
      />

      <InputTeks
        label="Nama jalan & nomor"
        id={`${idPrefix}-jalan`}
        value={nilai.jalan ?? ""}
        onChange={(e) => ubah({ jalan: e.target.value || null })}
        placeholder="mis. Jl. Raya Cikajang No. 12"
      />

      <button
        type="button"
        onClick={() => setRincianTerbuka((v) => !v)}
        className="inline-flex min-h-sentuh items-center justify-between rounded-lg border-2 border-kabut px-4 text-base font-semibold text-tanah/70 transition-colors duration-cepat hover:border-daun hover:text-daun"
        aria-expanded={rincianTerbuka}
      >
        Rincian lain (RT/RW, kode pos, patokan)
        {rincianTerbuka ? (
          <ChevronUp aria-hidden className="h-4 w-4" />
        ) : (
          <ChevronDown aria-hidden className="h-4 w-4" />
        )}
      </button>

      {rincianTerbuka && (
        <div className="flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-3">
            <InputTeks
              label="RT / RW"
              id={`${idPrefix}-rtrw`}
              value={nilai.rt_rw ?? ""}
              onChange={(e) => ubah({ rt_rw: e.target.value || null })}
              placeholder="003/005"
            />
            <InputTeks
              label="Kode pos"
              id={`${idPrefix}-kodepos`}
              inputMode="numeric"
              value={nilai.kode_pos ?? ""}
              onChange={(e) => ubah({ kode_pos: e.target.value || null })}
              placeholder="44171"
              className="angka"
            />
          </div>
          <InputTeks
            label="Patokan"
            id={`${idPrefix}-patokan`}
            value={nilai.patokan ?? ""}
            onChange={(e) => ubah({ patokan: e.target.value || null })}
            placeholder="mis. sebelah warung Bu Imas, pagar hijau"
          />
        </div>
      )}
    </section>
  );
}
