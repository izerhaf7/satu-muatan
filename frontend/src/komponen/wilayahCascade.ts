export type TingkatWilayah = "PROVINSI" | "KABUPATEN" | "KECAMATAN" | "DESA";

export interface WilayahAnak {
  kode: string;
  nama: string;
  tingkat: TingkatWilayah;
  jalur: string;
  kode_pos: string | null;
  lat: number | null;
  lng: number | null;
  induk_kode: string | null;
}

export interface NilaiWilayahCascade {
  provinsi: string | null;
  provinsiKode: string | null;
  kabupaten: string | null;
  kabupatenKode: string | null;
  kecamatan: string | null;
  kecamatanKode: string | null;
  desa: string | null;
  desaKode: string | null;
  kode_pos: string | null;
}

export interface PilihanWilayah {
  kode: string;
  nama: string;
  sementara: boolean;
}

export interface KodeWilayahTersimpan {
  kode: string;
  nama: string;
}

export interface StatusKodePos {
  nilai: string | null;
  otomatis: string | null;
}

interface GeokodeWilayah {
  provinsi: string | null;
  kabupaten: string | null;
  kecamatan: string | null;
  desa: string | null;
  kode_pos: string | null;
}

export function tingkatAnak(tingkat: TingkatWilayah): TingkatWilayah | null {
  const urutan: TingkatWilayah[] = ["PROVINSI", "KABUPATEN", "KECAMATAN", "DESA"];
  return urutan[urutan.indexOf(tingkat) + 1] ?? null;
}

export function buatPathWilayahAnak(tingkat: TingkatWilayah, indukKode?: string | null): string {
  const params = new URLSearchParams({ tingkat });
  if (indukKode) params.set("induk_kode", indukKode);
  return `/api/wilayah/anak?${params.toString()}`;
}

function namaNormal(nama: string): string {
  return nama.trim().toLocaleLowerCase("id");
}

export function cariKodeWilayah(nama: string | null, daftar: WilayahAnak[]): string | null {
  if (!nama) return null;
  const dicari = namaNormal(nama);
  return daftar.find((wilayah) => namaNormal(wilayah.nama) === dicari)?.kode ?? null;
}

export function kodeWilayahAktif(
  nama: string | null,
  tersimpan: KodeWilayahTersimpan | null,
  daftar: WilayahAnak[] | undefined,
): string | null {
  if (!nama) return null;
  if (daftar !== undefined) return cariKodeWilayah(nama, daftar);
  return tersimpan && namaNormal(tersimpan.nama) === namaNormal(nama) ? tersimpan.kode : null;
}

export function buatPilihanWilayah(nama: string | null, daftar: WilayahAnak[]): PilihanWilayah[] {
  const pilihan = daftar.map((wilayah) => ({
    kode: wilayah.kode,
    nama: wilayah.nama,
    sementara: false,
  }));
  if (nama && cariKodeWilayah(nama, daftar) === null) {
    pilihan.unshift({ kode: nama, nama, sementara: true });
  }
  return pilihan;
}

export function resetKodePosOtomatis(
  nilai: string | null,
  otomatis: string | null,
): StatusKodePos {
  return otomatis !== null && nilai === otomatis
    ? { nilai: null, otomatis: null }
    : { nilai, otomatis: null };
}

export function isiKodePosOtomatis(
  nilai: string | null,
  kodePosBaru: string | null,
): StatusKodePos {
  if (nilai || !kodePosBaru) return { nilai, otomatis: null };
  return { nilai: kodePosBaru, otomatis: kodePosBaru };
}

export function ubahKodePosManual(nilai: string | null): StatusKodePos {
  return { nilai, otomatis: null };
}

export function resetTurunanWilayah(
  nilai: NilaiWilayahCascade,
  tingkat: Exclude<TingkatWilayah, "DESA">,
  nama: string,
  kode: string,
): NilaiWilayahCascade {
  if (tingkat === "PROVINSI") {
    return {
      ...nilai,
      provinsi: nama,
      provinsiKode: kode,
      kabupaten: null,
      kabupatenKode: null,
      kecamatan: null,
      kecamatanKode: null,
      desa: null,
      desaKode: null,
    };
  }
  if (tingkat === "KABUPATEN") {
    return {
      ...nilai,
      kabupaten: nama,
      kabupatenKode: kode,
      kecamatan: null,
      kecamatanKode: null,
      desa: null,
      desaKode: null,
    };
  }
  return {
    ...nilai,
    kecamatan: nama,
    kecamatanKode: kode,
    desa: null,
    desaKode: null,
  };
}

export function pilihWilayah(nilai: NilaiWilayahCascade, wilayah: WilayahAnak): NilaiWilayahCascade {
  if (wilayah.tingkat === "DESA") {
    return {
      ...nilai,
      desa: wilayah.nama,
      desaKode: wilayah.kode,
      kode_pos: nilai.kode_pos || wilayah.kode_pos,
    };
  }
  return resetTurunanWilayah(nilai, wilayah.tingkat, wilayah.nama, wilayah.kode);
}

export function gantiWilayahDariGeokode(
  nilai: NilaiWilayahCascade,
  geokode: GeokodeWilayah,
): NilaiWilayahCascade {
  const hasil = { ...nilai };
  const tingkat = ["provinsi", "kabupaten", "kecamatan", "desa"] as const;

  for (const namaTingkat of tingkat) {
    if (geokode[namaTingkat] !== null) {
      hasil[namaTingkat] = geokode[namaTingkat];
      hasil[`${namaTingkat}Kode`] = null;
    }
  }
  if (geokode.kode_pos !== null) hasil.kode_pos = geokode.kode_pos;
  return hasil;
}
