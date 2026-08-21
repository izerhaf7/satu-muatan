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

import { useEffect, useRef, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

import InputTeks from "@/komponen/InputTeks";
import Select from "@/komponen/Select";
import type { components } from "@/api/client";
import { useCariWilayahAnak } from "@/hooks/useAlamat";
import {
  buatPilihanWilayah,
  isiKodePosOtomatis,
  kodeWilayahAktif,
  pilihWilayah,
  resetKodePosOtomatis,
  ubahKodePosManual,
  type KodeWilayahTersimpan,
  type NilaiWilayahCascade,
  type TingkatWilayah,
  type WilayahAnak,
} from "./wilayahCascade";

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

/** Hasil geokode mengganti hirarki lama agar alamat sesuai titik terkonfirmasi.
 *  Field manual lain tetap dipertahankan. */
export function terapkanGeokode(a: NilaiAlamat, g: GeokodeOut): NilaiAlamat {
  return {
    ...a,
    desa: g.desa ?? a.desa,
    kecamatan: g.kecamatan ?? a.kecamatan,
    kabupaten: g.kabupaten ?? a.kabupaten,
    provinsi: g.provinsi ?? a.provinsi,
    kode_pos: a.kode_pos || g.kode_pos || null,
    alamat: a.alamat || g.alamat,
  };
}

/** Wilayah yang dipilih mengisi komponen dari jalurnya, dari yang paling
 *  spesifik ke yang paling umum. */
export function terapkanWilayah(a: NilaiAlamat, w: WilayahOut): NilaiAlamat {
  const bagian = w.jalur.split(",").map((b: string) => b.trim());
  const dasar: NilaiAlamat = { ...a, kode_pos: a.kode_pos || w.kode_pos || null };

  if (w.tingkat === "DESA") {
    return { ...dasar, desa: bagian[0] ?? null, kecamatan: bagian[1] ?? null, kabupaten: bagian[2] ?? null, provinsi: bagian[3] ?? null };
  }
  if (w.tingkat === "KECAMATAN") {
    return { ...dasar, kecamatan: bagian[0] ?? null, kabupaten: bagian[1] ?? null, provinsi: bagian[2] ?? null };
  }
  return { ...dasar, kabupaten: bagian[0] ?? null, provinsi: bagian[1] ?? null };
}

function placeholderWilayah(
  siap: boolean,
  sedangMemuat: boolean,
  galat: boolean,
  kosong: boolean,
  pilih: string,
  prasyarat: string,
): string {
  if (!siap) return prasyarat;
  if (sedangMemuat) return "Memuat…";
  if (galat) return "Gagal memuat wilayah";
  if (kosong) return "Wilayah tidak tersedia";
  return pilih;
}

interface FormAlamatProps {
  judul: string;
  /** Menandai apakah alamat ini wajib untuk membuat kiriman. */
  wajib: boolean;
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
  wajib,
  idPrefix,
  nilai,
  onUbah,
  labelNama,
  labelTelepon,
  onWilayahBerkoordinat,
  keterangan,
}: FormAlamatProps) {
  const [rincianTerbuka, setRincianTerbuka] = useState(false);
  const [kodeWilayah, setKodeWilayah] = useState({
    provinsi: null as KodeWilayahTersimpan | null,
    kabupaten: null as KodeWilayahTersimpan | null,
    kecamatan: null as KodeWilayahTersimpan | null,
    desa: null as KodeWilayahTersimpan | null,
  });
  const kodePosOtomatis = useRef<string | null>(null);
  const kodePosSebelumnya = useRef(nilai.kode_pos ?? null);
  const kodePosSaatIni = nilai.kode_pos ?? null;

  useEffect(() => {
    if (kodePosSebelumnya.current === null && kodePosSaatIni !== null && kodePosOtomatis.current === null) {
      kodePosOtomatis.current = kodePosSaatIni;
    }
    kodePosSebelumnya.current = kodePosSaatIni;
  }, [kodePosSaatIni]);

  const provinsi = useCariWilayahAnak("PROVINSI");
  const provinsiKode = kodeWilayahAktif(nilai.provinsi ?? null, kodeWilayah.provinsi, provinsi.data);
  const kabupaten = useCariWilayahAnak("KABUPATEN", provinsiKode);
  const kabupatenKode = kodeWilayahAktif(nilai.kabupaten ?? null, kodeWilayah.kabupaten, kabupaten.data);
  const kecamatan = useCariWilayahAnak("KECAMATAN", kabupatenKode);
  const kecamatanKode = kodeWilayahAktif(nilai.kecamatan ?? null, kodeWilayah.kecamatan, kecamatan.data);
  const desa = useCariWilayahAnak("DESA", kecamatanKode);
  const desaKode = kodeWilayahAktif(nilai.desa ?? null, kodeWilayah.desa, desa.data);

  function ubah(bagian: Partial<NilaiAlamat>) {
    onUbah({ ...nilai, ...bagian });
  }

  function ubahWilayah(wilayah: WilayahAnak) {
    const cascade: NilaiWilayahCascade = {
      provinsi: nilai.provinsi ?? null,
      provinsiKode,
      kabupaten: nilai.kabupaten ?? null,
      kabupatenKode,
      kecamatan: nilai.kecamatan ?? null,
      kecamatanKode,
      desa: nilai.desa ?? null,
      desaKode,
      kode_pos: nilai.kode_pos ?? null,
    };
    const hasil = pilihWilayah(cascade, wilayah);
    const statusKodePos =
      wilayah.tingkat === "DESA"
        ? isiKodePosOtomatis(nilai.kode_pos ?? null, wilayah.kode_pos)
        : resetKodePosOtomatis(nilai.kode_pos ?? null, kodePosOtomatis.current);
    kodePosOtomatis.current = statusKodePos.otomatis;
    setKodeWilayah({
      provinsi:
        hasil.provinsiKode && hasil.provinsi ? { kode: hasil.provinsiKode, nama: hasil.provinsi } : null,
      kabupaten:
        hasil.kabupatenKode && hasil.kabupaten ? { kode: hasil.kabupatenKode, nama: hasil.kabupaten } : null,
      kecamatan:
        hasil.kecamatanKode && hasil.kecamatan ? { kode: hasil.kecamatanKode, nama: hasil.kecamatan } : null,
      desa: hasil.desaKode && hasil.desa ? { kode: hasil.desaKode, nama: hasil.desa } : null,
    });
    onUbah({
      ...nilai,
      provinsi: hasil.provinsi,
      kabupaten: hasil.kabupaten,
      kecamatan: hasil.kecamatan,
      desa: hasil.desa,
      kode_pos: statusKodePos.nilai,
    });
    if (wilayah.lat != null && wilayah.lng != null && Number.isFinite(wilayah.lat) && Number.isFinite(wilayah.lng)) {
      onWilayahBerkoordinat?.({ lat: wilayah.lat, lng: wilayah.lng });
    }
  }

  function saatPilih(tingkat: TingkatWilayah, kode: string, daftar: WilayahAnak[] | undefined) {
    const wilayah = daftar?.find((pilihan) => pilihan.kode === kode);
    if (wilayah && wilayah.tingkat === tingkat) ubahWilayah(wilayah);
  }

  return (
    <section aria-label={judul} className="flex flex-col gap-3">
      <div className="flex flex-col gap-0.5">
        <div className="flex items-center gap-2">
          <h3 className="text-subjudul text-tanah">{judul}</h3>
          <span
            className={`rounded-full px-2 py-0.5 text-keterangan font-semibold ${
              wajib ? "bg-tanah-liat/10 text-tanah-liat" : "bg-tanah/5 text-tanah/60"
            }`}
          >
            {wajib ? "Wajib" : "Opsional"}
          </span>
        </div>
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

      <div className="grid grid-cols-1 gap-3">
        <Select
          label="Provinsi"
          id={`${idPrefix}-provinsi`}
          value={provinsiKode ?? nilai.provinsi ?? ""}
          onChange={(e) => saatPilih("PROVINSI", e.target.value, provinsi.data)}
          disabled={provinsi.isLoading || provinsi.isError || provinsi.data?.length === 0}
        >
          <option value="" disabled>
            {placeholderWilayah(true, provinsi.isLoading, provinsi.isError, provinsi.data?.length === 0, "Pilih provinsi", "")}
          </option>
          {buatPilihanWilayah(nilai.provinsi ?? null, provinsi.data ?? []).map((pilihan) => (
            <option key={`${pilihan.sementara ? "sementara" : "wilayah"}-${pilihan.kode}`} value={pilihan.kode}>
              {pilihan.nama}
            </option>
          ))}
        </Select>
        <Select
          label="Kabupaten / Kota"
          id={`${idPrefix}-kabupaten`}
          value={kabupatenKode ?? nilai.kabupaten ?? ""}
          onChange={(e) => saatPilih("KABUPATEN", e.target.value, kabupaten.data)}
          disabled={!provinsiKode || kabupaten.isLoading || kabupaten.isError || kabupaten.data?.length === 0}
        >
          <option value="" disabled>
            {placeholderWilayah(
              Boolean(provinsiKode),
              kabupaten.isLoading,
              kabupaten.isError,
              kabupaten.data?.length === 0,
              "Pilih kabupaten / kota",
              "Pilih provinsi dahulu",
            )}
          </option>
          {buatPilihanWilayah(nilai.kabupaten ?? null, kabupaten.data ?? []).map((pilihan) => (
            <option key={`${pilihan.sementara ? "sementara" : "wilayah"}-${pilihan.kode}`} value={pilihan.kode}>
              {pilihan.nama}
            </option>
          ))}
        </Select>
        <Select
          label="Kecamatan"
          id={`${idPrefix}-kecamatan`}
          value={kecamatanKode ?? nilai.kecamatan ?? ""}
          onChange={(e) => saatPilih("KECAMATAN", e.target.value, kecamatan.data)}
          disabled={!kabupatenKode || kecamatan.isLoading || kecamatan.isError || kecamatan.data?.length === 0}
        >
          <option value="" disabled>
            {placeholderWilayah(
              Boolean(kabupatenKode),
              kecamatan.isLoading,
              kecamatan.isError,
              kecamatan.data?.length === 0,
              "Pilih kecamatan",
              "Pilih kabupaten / kota dahulu",
            )}
          </option>
          {buatPilihanWilayah(nilai.kecamatan ?? null, kecamatan.data ?? []).map((pilihan) => (
            <option key={`${pilihan.sementara ? "sementara" : "wilayah"}-${pilihan.kode}`} value={pilihan.kode}>
              {pilihan.nama}
            </option>
          ))}
        </Select>
        <Select
          label="Desa / Kelurahan"
          id={`${idPrefix}-desa`}
          value={desaKode ?? nilai.desa ?? ""}
          onChange={(e) => saatPilih("DESA", e.target.value, desa.data)}
          disabled={!kecamatanKode || desa.isLoading || desa.isError || desa.data?.length === 0}
        >
          <option value="" disabled>
            {placeholderWilayah(
              Boolean(kecamatanKode),
              desa.isLoading,
              desa.isError,
              desa.data?.length === 0,
              "Pilih desa / kelurahan",
              "Pilih kecamatan dahulu",
            )}
          </option>
          {buatPilihanWilayah(nilai.desa ?? null, desa.data ?? []).map((pilihan) => (
            <option key={`${pilihan.sementara ? "sementara" : "wilayah"}-${pilihan.kode}`} value={pilihan.kode}>
              {pilihan.nama}
            </option>
          ))}
        </Select>
      </div>

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
              onChange={(e) => {
                const statusKodePos = ubahKodePosManual(e.target.value || null);
                kodePosOtomatis.current = statusKodePos.otomatis;
                kodePosSebelumnya.current = statusKodePos.nilai;
                ubah({ kode_pos: statusKodePos.nilai });
              }}
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
