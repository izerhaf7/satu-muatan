import { describe, expect, it } from "vitest";

import type { NilaiAlamat } from "@/komponen/FormAlamat";

import {
  bersihkanFieldProvider,
  buatKunciKoordinat,
  bolehTerapkanResponsGeokode,
  catatFieldProvider,
  pulihkanAlamatSaatBatal,
} from "./geokodeTitik";

const ALAMAT: NilaiAlamat = {
  alamat: "Jl. Provider 1",
  nama: "Bu Rina",
  telepon: "081200000021",
  jalan: "Jl. Manual 2",
  rt_rw: "001/002",
  desa: "Desa Provider",
  kecamatan: "Kecamatan Manual",
  kabupaten: "Kabupaten Provider",
  provinsi: "Jawa Barat",
  kode_pos: "40123",
  patokan: "Pagar hijau",
};

describe("identitas koordinat geokode", () => {
  it("membuat kunci dari koordinat persis", () => {
    expect(buatKunciKoordinat({ lat: -6.9, lng: 107.6 })).toBe("-6.9,107.6");
    expect(buatKunciKoordinat(null)).toBeNull();
  });

  it("menolak respons lama setelah titik aktif berubah", () => {
    const kunciLama = buatKunciKoordinat({ lat: -6.9, lng: 107.6 });
    expect(bolehTerapkanResponsGeokode(kunciLama, { lat: -6.8, lng: 107.7 })).toBe(false);
  });

  it("menerima respons untuk titik aktif yang sama", () => {
    const titik = { lat: -6.9, lng: 107.6 };
    expect(bolehTerapkanResponsGeokode(buatKunciKoordinat(titik), titik)).toBe(true);
  });
});

describe("provenance field geokode", () => {
  it("membersihkan nilai lama dari provider tetapi mempertahankan field manual", () => {
    const jejak = catatFieldProvider({
      alamat: "Jl. Provider 1",
      desa: "Desa Provider",
      kecamatan: "Kecamatan Provider",
      kabupaten: "Kabupaten Provider",
      provinsi: "Jawa Barat",
      kode_pos: "44171",
    });

    expect(bersihkanFieldProvider(ALAMAT, jejak)).toEqual({
      ...ALAMAT,
      alamat: "",
      desa: null,
      kabupaten: null,
      provinsi: null,
    });
  });

  it("membersihkan kode pos provider dan mempertahankan kode pos yang diedit manual", () => {
    const jejak = catatFieldProvider({ kode_pos: "44171" });
    expect(bersihkanFieldProvider({ ...ALAMAT, kode_pos: "44171" }, jejak).kode_pos).toBeNull();
    expect(bersihkanFieldProvider({ ...ALAMAT, kode_pos: "40123" }, jejak).kode_pos).toBe("40123");
  });

  it("memulihkan snapshot alamat saat perubahan wilayah dibatalkan", () => {
    expect(pulihkanAlamatSaatBatal({ ...ALAMAT, desa: "Desa Kandidat" }, ALAMAT)).toEqual(ALAMAT);
    expect(pulihkanAlamatSaatBatal(ALAMAT, null)).toBe(ALAMAT);
  });
});
