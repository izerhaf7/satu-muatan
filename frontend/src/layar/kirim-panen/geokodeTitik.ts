import type { NilaiAlamat } from "@/komponen/FormAlamat";

type FieldProvider = "alamat" | "jalan" | "desa" | "kecamatan" | "kabupaten" | "provinsi" | "kode_pos";

export type JejakFieldProvider = Partial<Pick<NilaiAlamat, FieldProvider>>;

type HasilProvider = Partial<Record<FieldProvider, string | null>>;

export function buatKunciKoordinat(titik: { lat: number; lng: number } | null): string | null {
  return titik ? `${titik.lat},${titik.lng}` : null;
}

export function bolehTerapkanResponsGeokode(
  kunciRespons: string | null,
  titikAktif: { lat: number; lng: number } | null,
): boolean {
  return kunciRespons !== null && kunciRespons === buatKunciKoordinat(titikAktif);
}

export function catatFieldProvider(hasil: HasilProvider, alamatSebelum?: NilaiAlamat): JejakFieldProvider {
  const jejak: JejakFieldProvider = {};
  const fieldWilayah: FieldProvider[] = ["desa", "kecamatan", "kabupaten", "provinsi"];

  for (const field of fieldWilayah) {
    if (hasil[field]) jejak[field] = hasil[field];
  }
  if (hasil.alamat && !alamatSebelum?.alamat) jejak.alamat = hasil.alamat;
  if (hasil.kode_pos && !alamatSebelum?.kode_pos) jejak.kode_pos = hasil.kode_pos;
  return jejak;
}

export function bersihkanFieldProvider(alamat: NilaiAlamat, jejak: JejakFieldProvider): NilaiAlamat {
  const hasil = { ...alamat };
  for (const field of Object.keys(jejak) as FieldProvider[]) {
    if (hasil[field] !== jejak[field]) continue;
    if (field === "alamat") hasil.alamat = "";
    else hasil[field] = null;
  }
  return hasil;
}

export function pulihkanAlamatSaatBatal(alamat: NilaiAlamat, snapshot: NilaiAlamat | null): NilaiAlamat {
  return snapshot ?? alamat;
}
