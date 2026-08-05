import { describe, expect, it, vi } from "vitest";

import type { components } from "@/api/client";
import {
  BATAS_SARAN_ALAMAT,
  DURASI_DEBOUNCE_ALAMAT_MS,
  KELAS_BARIS_SARAN_ALAMAT,
  buatGenerasiPencarian,
  buatStatusCariAlamat,
  gerakkanSorotan,
  hitungKarakterUnicode,
  jadwalkanPencarianAlamat,
  normalisasiSaran,
  bolehCariAlamat,
  bolehTerapkanResolusiAlamat,
  terapkanResolusiAlamat,
} from "./CariAlamat";

type AlamatResolusiOut = components["schemas"]["AlamatResolusiOut"];

describe("CariAlamat", () => {
  it("menunggu 300 ms dan mensyaratkan tiga karakter Unicode setelah trim", () => {
    expect(DURASI_DEBOUNCE_ALAMAT_MS).toBe(300);
    expect(hitungKarakterUnicode("  Jl ")).toBe(2);
    expect(hitungKarakterUnicode("  茂名市 ")).toBe(3);
    expect(buatStatusCariAlamat(" Jl ", false, false, undefined)).toEqual({ jenis: "PETUNJUK" });
  });

  it("baru menjalankan pencarian pada 300 ms dan dapat membatalkan jadwal lama", () => {
    vi.useFakeTimers();
    const cari = vi.fn();
    const batalPendek = jadwalkanPencarianAlamat(" Jl ", cari);
    vi.advanceTimersByTime(300);
    expect(cari).not.toHaveBeenCalled();
    batalPendek();

    const batal = jadwalkanPencarianAlamat(" Braga ", cari);
    vi.advanceTimersByTime(299);
    expect(cari).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(cari).toHaveBeenCalledWith("Braga");
    batal();

    const batalLama = jadwalkanPencarianAlamat("Bandung", cari);
    batalLama();
    vi.advanceTimersByTime(300);
    expect(cari).toHaveBeenCalledTimes(1);
    vi.useRealTimers();
  });

  it("menolak hasil generasi lama dan membatasi lima saran", () => {
    const generasi = buatGenerasiPencarian();
    const lama = generasi.mulai();
    const baru = generasi.mulai();
    expect(generasi.masihAktif(lama)).toBe(false);
    expect(generasi.masihAktif(baru)).toBe(true);
    expect(normalisasiSaran(Array.from({ length: 8 }, (_, i) => ({ place_id: String(i) })))).toHaveLength(
      BATAS_SARAN_ALAMAT,
    );
  });

  it("tidak mencari alamat asal tanpa opt-in eksplisit", () => {
    expect(bolehCariAlamat("Bandung", false)).toBe(false);
    expect(bolehCariAlamat("Bandung", true)).toBe(true);
    expect(bolehCariAlamat("Jl", true)).toBe(false);
  });

  it("membedakan loading, kosong, jaringan, dan fallback penyedia", () => {
    expect(buatStatusCariAlamat("Bandung", true, false, undefined)).toEqual({ jenis: "MEMUAT" });
    expect(buatStatusCariAlamat("Bandung", false, true, undefined)).toEqual({ jenis: "JARINGAN" });
    expect(
      buatStatusCariAlamat("Bandung", false, false, {
        saran: [],
        status: "PENYEDIA_TIDAK_TERSEDIA",
        pesan: "Isi alamat secara manual.",
      }),
    ).toEqual({ jenis: "FALLBACK", pesan: "Isi alamat secara manual." });
    expect(
      buatStatusCariAlamat("Bandung", false, false, { saran: [], status: "TIDAK_DITEMUKAN" }),
    ).toEqual({ jenis: "KOSONG" });
  });

  it("menggerakkan sorotan Arrow dan menutupnya dengan Escape", () => {
    expect(gerakkanSorotan(-1, "ArrowDown", 3)).toBe(0);
    expect(gerakkanSorotan(0, "ArrowUp", 3)).toBe(2);
    expect(gerakkanSorotan(2, "ArrowDown", 3)).toBe(0);
    expect(gerakkanSorotan(1, "Escape", 3)).toBe(-1);
    expect(gerakkanSorotan(1, "Enter", 3)).toBe(1);
  });

  it("menjaga setiap baris saran setinggi minimal 48 px", () => {
    expect(KELAS_BARIS_SARAN_ALAMAT).toContain("min-h-sentuh");
  });

  it("mengisi field normalisasi, mempertahankan edit manual, dan menyiapkan koordinat pending", () => {
    const resolusi: AlamatResolusiOut = {
      alamat_lengkap: "Jl. Braga 10, Bandung",
      jalan: "Jl. Braga 10",
      desa: "Braga",
      kecamatan: "Sumur Bandung",
      kabupaten_kota: "Kota Bandung",
      provinsi: "Jawa Barat",
      kode_pos: "40111",
      lat: -6.917,
      lng: 107.609,
      granularitas: "ALAMAT",
      sumber: "GOOGLE",
      status: "OK",
    };
    const hasil = terapkanResolusiAlamat(
      {
        alamat: "",
        nama: "Bu Rina",
        telepon: null,
        jalan: "Jalan manual",
        rt_rw: null,
        desa: null,
        kecamatan: null,
        kabupaten: null,
        provinsi: null,
        kode_pos: "40115",
        patokan: "Pagar hijau",
      },
      resolusi,
    );
    expect(hasil.alamat).toMatchObject({
      alamat: "Jl. Braga 10, Bandung",
      jalan: "Jalan manual",
      desa: "Braga",
      kecamatan: "Sumur Bandung",
      kabupaten: "Kota Bandung",
      provinsi: "Jawa Barat",
      kode_pos: "40115",
      patokan: "Pagar hijau",
    });
    expect(hasil.titikPending).toEqual({
      lat: -6.917,
      lng: 107.609,
      sumber: "ALAMAT",
      alamat: "Jl. Braga 10, Bandung",
    });
    expect(hasil.peringatan).toBeNull();
  });

  it("memberi peringatan koordinat kasar atau kosong tanpa menghapus isian manual", () => {
    const alamat = {
      alamat: "Alamat manual",
      nama: null,
      telepon: null,
      jalan: "Jalan manual",
      rt_rw: null,
      desa: null,
      kecamatan: null,
      kabupaten: null,
      provinsi: null,
      kode_pos: null,
      patokan: null,
    };
    const kasar = terapkanResolusiAlamat(alamat, {
      alamat_lengkap: "Bandung",
      sumber: "LOKAL",
      status: "KOORDINAT_TIDAK_PRESISI",
      granularitas: "KABUPATEN_KOTA",
      lat: -6.9,
      lng: 107.6,
      pesan: "Titik masih perkiraan.",
    });
    expect(kasar.alamat.jalan).toBe("Jalan manual");
    expect(kasar.peringatan).toContain("Titik masih perkiraan");
    expect(kasar.titikPending).not.toBeNull();

    const tanpaTitik = terapkanResolusiAlamat(alamat, {
      alamat_lengkap: "Bandung",
      sumber: "LOKAL",
      status: "KOORDINAT_TIDAK_PRESISI",
      granularitas: "KABUPATEN_KOTA",
      pesan: "Koordinat tidak tersedia.",
    });
    expect(tanpaTitik.alamat.jalan).toBe("Jalan manual");
    expect(tanpaTitik.titikPending).toBeNull();
    expect(tanpaTitik.peringatan).toContain("Pilih titik lewat peta");
  });

  it("menerapkan pemilihan hanya sekali untuk generasi resolusi aktif", async () => {
    const generasi = buatGenerasiPencarian();
    const panggil = vi.fn();
    const pertama = generasi.mulai();
    panggil();
    expect(generasi.masihAktif(pertama)).toBe(true);
    generasi.batalkan();
    expect(generasi.masihAktif(pertama)).toBe(false);
    expect(panggil).toHaveBeenCalledTimes(1);
  });

  it("menolak resolusi saat alamat atau titik tujuan berubah selama permintaan", () => {
    expect(bolehTerapkanResolusiAlamat(true, 4, 4)).toBe(true);
    expect(bolehTerapkanResolusiAlamat(true, 4, 5)).toBe(false);
    expect(bolehTerapkanResolusiAlamat(false, 4, 4)).toBe(false);
  });
});
