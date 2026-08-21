import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { AlertTriangle, LoaderCircle, MapPin, Search } from "lucide-react";

import type { components } from "@/api/client";
import {
  useResolusiAlamat,
  useSaranAlamat,
  type AlamatSaranItem,
  type AlamatSaranList,
} from "@/hooks/useAlamat";
import type { Titik } from "@/layar/kirim-panen/PetaPilihTitik";
import { bersihkanFieldProvider, type JejakFieldProvider } from "@/layar/kirim-panen/geokodeTitik";
import type { NilaiAlamat } from "./FormAlamat";

export const DURASI_DEBOUNCE_ALAMAT_MS = 300;
export const BATAS_SARAN_ALAMAT = 5;
export const KELAS_BARIS_SARAN_ALAMAT =
  "flex min-h-sentuh w-full items-start gap-3 px-4 py-3 text-left hover:bg-daun/5 focus:bg-daun/10 focus:outline-none disabled:cursor-wait";

export function hitungKarakterUnicode(teks: string): number {
  return Array.from(teks.trim()).length;
}

export function bolehCariAlamat(query: string, aktif: boolean): boolean {
  return aktif && hitungKarakterUnicode(query) >= 3;
}

export function bolehTerapkanResolusiAlamat(
  generasiAktif: boolean,
  revisiSaatMulai: number,
  revisiSaatIni: number,
): boolean {
  return generasiAktif && revisiSaatMulai === revisiSaatIni;
}

export function jadwalkanPencarianAlamat(query: string, jalankan: (query: string) => void): () => void {
  const bersih = query.trim();
  if (hitungKarakterUnicode(bersih) < 3) return () => undefined;
  const timer = globalThis.setTimeout(() => jalankan(bersih), DURASI_DEBOUNCE_ALAMAT_MS);
  return () => globalThis.clearTimeout(timer);
}

export function normalisasiSaran<T>(saran: T[]): T[] {
  return saran.slice(0, BATAS_SARAN_ALAMAT);
}

export function buatGenerasiPencarian() {
  let aktif = 0;
  return {
    mulai() {
      aktif += 1;
      return aktif;
    },
    batalkan() {
      aktif += 1;
    },
    masihAktif(generasi: number) {
      return generasi === aktif;
    },
  };
}

export function gerakkanSorotan(aktif: number, tombol: string, jumlah: number): number {
  if (tombol === "Escape" || jumlah === 0) return -1;
  if (tombol === "ArrowDown") return (aktif + 1 + jumlah) % jumlah;
  if (tombol === "ArrowUp") return (aktif - 1 + jumlah) % jumlah;
  return aktif;
}

export type StatusCariAlamat =
  | { jenis: "PETUNJUK" | "MEMUAT" | "KOSONG" | "JARINGAN" }
  | { jenis: "FALLBACK"; pesan: string };

export function buatStatusCariAlamat(
  query: string,
  sedangMemuat: boolean,
  galat: boolean,
  data: AlamatSaranList | undefined,
): StatusCariAlamat | null {
  if (hitungKarakterUnicode(query) < 3) return { jenis: "PETUNJUK" };
  if (sedangMemuat) return { jenis: "MEMUAT" };
  if (galat) return { jenis: "JARINGAN" };
  if (data?.status === "PENYEDIA_TIDAK_TERSEDIA" || data?.status === "FALLBACK_LOKAL") {
    return { jenis: "FALLBACK", pesan: data.pesan ?? "Gunakan pilihan lokal atau isi alamat secara manual." };
  }
  if (data && data.saran.length === 0) return { jenis: "KOSONG" };
  return null;
}

export function terapkanResolusiAlamat(
  nilai: NilaiAlamat,
  hasil: components["schemas"]["AlamatResolusiOut"],
  jejakSebelumnya: JejakFieldProvider = {},
) {
  const dasar = bersihkanFieldProvider(nilai, jejakSebelumnya);
  const alamat: NilaiAlamat = {
    ...dasar,
    alamat: dasar.alamat || hasil.alamat_lengkap || "",
    jalan: dasar.jalan || hasil.jalan || null,
    desa: dasar.desa || hasil.desa || null,
    kecamatan: dasar.kecamatan || hasil.kecamatan || null,
    kabupaten: dasar.kabupaten || hasil.kabupaten_kota || null,
    provinsi: dasar.provinsi || hasil.provinsi || null,
    kode_pos: dasar.kode_pos || hasil.kode_pos || null,
  };
  const lat = hasil.lat;
  const lng = hasil.lng;
  const punyaKoordinat = typeof lat === "number" && typeof lng === "number";
  const titikPending: Titik | null = punyaKoordinat
    ? { lat, lng, sumber: "ALAMAT", alamat: hasil.alamat_lengkap ?? undefined }
    : null;
  const jejak: JejakFieldProvider = {};
  if (!dasar.alamat && hasil.alamat_lengkap) jejak.alamat = hasil.alamat_lengkap;
  if (!dasar.jalan && hasil.jalan) jejak.jalan = hasil.jalan;
  if (!dasar.desa && hasil.desa) jejak.desa = hasil.desa;
  if (!dasar.kecamatan && hasil.kecamatan) jejak.kecamatan = hasil.kecamatan;
  if (!dasar.kabupaten && hasil.kabupaten_kota) jejak.kabupaten = hasil.kabupaten_kota;
  if (!dasar.provinsi && hasil.provinsi) jejak.provinsi = hasil.provinsi;
  if (!dasar.kode_pos && hasil.kode_pos) jejak.kode_pos = hasil.kode_pos;
  let peringatan: string | null = null;
  if (hasil.status === "KOORDINAT_TIDAK_PRESISI") {
    peringatan = punyaKoordinat
      ? `${hasil.pesan ?? "Koordinat alamat masih perkiraan."} Geser pin bila perlu, lalu konfirmasi.`
      : `${hasil.pesan ?? "Koordinat alamat tidak tersedia."} Pilih titik lewat peta.`;
  } else if (!punyaKoordinat) {
    peringatan = "Koordinat alamat tidak tersedia. Pilih titik lewat peta.";
  }
  return { alamat, titikPending, peringatan, jejak };
}

interface CariAlamatProps {
  id: string;
  nilai: NilaiAlamat;
  onUbah: (alamat: NilaiAlamat) => void;
  onPilihTitik: (titik: Titik) => void;
  onPeringatan?: (pesan: string | null) => void;
  jejakProvider?: JejakFieldProvider;
  onJejakProvider?: (jejak: JejakFieldProvider) => void;
  label?: string;
  aktif?: boolean;
  dapatkanRevisiTujuan?: () => number;
}

export default function CariAlamat({
  id,
  nilai,
  onUbah,
  onPilihTitik,
  onPeringatan,
  jejakProvider = {},
  onJejakProvider,
  label = "Cari alamat tujuan",
  aktif = true,
  dapatkanRevisiTujuan = () => 0,
}: CariAlamatProps) {
  const listboxId = `${useId()}-saran-alamat`;
  const [query, setQuery] = useState("");
  const [queryDebounce, setQueryDebounce] = useState("");
  const [sorotan, setSorotan] = useState(-1);
  const [terbuka, setTerbuka] = useState(false);
  const generasiResolusi = useRef(buatGenerasiPencarian());
  const abortResolusi = useRef<AbortController | null>(null);
  const sedangMemilih = useRef(false);
  const saran = useSaranAlamat(queryDebounce, bolehCariAlamat(queryDebounce, aktif));
  const resolusi = useResolusiAlamat();
  const daftar = normalisasiSaran(saran.data?.saran ?? []);
  const status = buatStatusCariAlamat(queryDebounce, saran.isLoading, saran.isError, saran.data);

  useEffect(() => {
    const bersih = query.trim();
    if (!bolehCariAlamat(bersih, aktif)) {
      setQueryDebounce("");
      setTerbuka(false);
      return;
    }
    return jadwalkanPencarianAlamat(bersih, (querySiap) => {
      setQueryDebounce(querySiap);
      setTerbuka(true);
    });
  }, [aktif, query]);

  useEffect(() => {
    setSorotan(-1);
  }, [queryDebounce, saran.data]);

  useEffect(
    () => () => {
      generasiResolusi.current.batalkan();
      abortResolusi.current?.abort();
    },
    [],
  );

  async function pilih(item: AlamatSaranItem) {
    if (sedangMemilih.current) return;
    sedangMemilih.current = true;
    const generasi = generasiResolusi.current.mulai();
    const revisiSaatMulai = dapatkanRevisiTujuan();
    abortResolusi.current?.abort();
    const controller = new AbortController();
    abortResolusi.current = controller;
    setQuery(item.teks_lengkap);
    setTerbuka(false);
    try {
      const hasil = await resolusi.mutateAsync({ placeId: item.place_id, signal: controller.signal });
      if (
        !bolehTerapkanResolusiAlamat(
          generasiResolusi.current.masihAktif(generasi),
          revisiSaatMulai,
          dapatkanRevisiTujuan(),
        )
      )
        return;
      const diterapkan = terapkanResolusiAlamat(nilai, hasil, jejakProvider);
      onUbah(diterapkan.alamat);
      onPeringatan?.(diterapkan.peringatan);
      if (diterapkan.titikPending) onPilihTitik(diterapkan.titikPending);
      onJejakProvider?.(diterapkan.jejak);
    } catch {
      if (
        controller.signal.aborted ||
        !bolehTerapkanResolusiAlamat(
          generasiResolusi.current.masihAktif(generasi),
          revisiSaatMulai,
          dapatkanRevisiTujuan(),
        )
      )
        return;
      onPeringatan?.("Alamat belum dapat dibaca. Isian manual tetap tersimpan; pilih wilayah atau titik lewat peta.");
    } finally {
      if (generasiResolusi.current.masihAktif(generasi)) sedangMemilih.current = false;
    }
  }

  function saatTombol(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Escape") {
      e.preventDefault();
      setTerbuka(false);
      setSorotan(-1);
      return;
    }
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      setTerbuka(true);
      setSorotan((aktif) => gerakkanSorotan(aktif, e.key, daftar.length));
      return;
    }
    if (e.key === "Enter" && terbuka && sorotan >= 0 && daftar[sorotan]) {
      e.preventDefault();
      void pilih(daftar[sorotan]);
    }
  }

  const idAktif = sorotan >= 0 && daftar[sorotan] ? `${listboxId}-${sorotan}` : undefined;
  const tampilkanStatus = terbuka && status;
  const adaGoogle = daftar.some((item) => item.sumber === "GOOGLE");

  return (
    <div className="relative flex flex-col gap-1.5">
      <label htmlFor={id} className="text-keterangan font-semibold text-tanah">
        {label}
      </label>
      <div className="relative">
        <Search aria-hidden className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-tanah/40" />
        <input
          id={id}
          role="combobox"
          aria-autocomplete="list"
          aria-controls={listboxId}
          aria-expanded={terbuka}
          aria-activedescendant={idAktif}
          aria-busy={saran.isLoading || resolusi.isPending || undefined}
          value={query}
          onChange={(e) => {
            generasiResolusi.current.batalkan();
            abortResolusi.current?.abort();
            sedangMemilih.current = false;
            setQuery(e.target.value);
            setTerbuka(false);
            setSorotan(-1);
          }}
          onFocus={() => queryDebounce && setTerbuka(true)}
          onKeyDown={saatTombol}
          autoComplete="off"
          placeholder="Ketik jalan, gedung, atau alamat"
          className="min-h-sentuh w-full rounded-lg border-2 border-kabut bg-kertas py-2 pl-11 pr-4 text-base text-tanah placeholder:text-tanah/40 transition-colors duration-cepat hover:border-tanah/30 focus:border-daun focus:outline-none focus:ring-2 focus:ring-daun/25"
        />
      </div>
      <p className="text-keterangan text-tanah/55">Minimal 3 karakter. Saran diproses lewat server Satu Muatan.</p>

      {terbuka && (daftar.length > 0 || tampilkanStatus) && (
        <div className="absolute inset-x-0 top-full z-30 mt-1 overflow-hidden rounded-xl border-2 border-kabut bg-kertas shadow-angkat">
          {daftar.length > 0 && (
            <ul id={listboxId} role="listbox" aria-label="Saran alamat" className="divide-y divide-kabut">
              {daftar.map((item: AlamatSaranItem, index: number) => (
                <li
                  key={`${item.sumber}-${item.place_id}`}
                  role="presentation"
                >
                  <button
                    id={`${listboxId}-${index}`}
                    type="button"
                    role="option"
                    aria-selected={sorotan === index}
                    onMouseDown={(e) => e.preventDefault()}
                    onClick={() => void pilih(item)}
                    disabled={resolusi.isPending}
                    className={`${KELAS_BARIS_SARAN_ALAMAT} ${sorotan === index ? "bg-daun/10" : "bg-kertas"}`}
                  >
                    <MapPin aria-hidden className="mt-0.5 h-5 w-5 shrink-0 text-daun" />
                    <span className="min-w-0">
                      <span className="block font-semibold text-tanah">{item.teks_utama}</span>
                      <span className="block text-keterangan text-tanah/60">{item.teks_lengkap}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {tampilkanStatus && (
            <div role={status.jenis === "JARINGAN" || status.jenis === "FALLBACK" ? "alert" : "status"} className="flex min-h-sentuh items-start gap-2 px-4 py-3 text-keterangan text-tanah/70">
              {status.jenis === "MEMUAT" && <LoaderCircle aria-hidden className="h-4 w-4 animate-spin" />}
              {(status.jenis === "JARINGAN" || status.jenis === "FALLBACK") && <AlertTriangle aria-hidden className="h-4 w-4 shrink-0 text-tanah-liat" />}
              <span>
                {status.jenis === "PETUNJUK" && "Ketik minimal 3 karakter."}
                {status.jenis === "MEMUAT" && "Mencari alamat…"}
                {status.jenis === "KOSONG" && "Alamat tidak ditemukan. Pilih wilayah atau isi manual."}
                {status.jenis === "JARINGAN" && "Jaringan bermasalah. Isian wilayah dan peta tetap dapat digunakan."}
                {status.jenis === "FALLBACK" && status.pesan}
              </span>
            </div>
          )}
          {adaGoogle && <p className="border-t border-kabut px-4 py-2 text-right text-keterangan font-semibold text-tanah/60">Didukung oleh Google</p>}
        </div>
      )}
    </div>
  );
}
