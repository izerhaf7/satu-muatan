import { describe, expect, it } from "vitest";

import {
  adaTitikPending,
  batalkanTitikPending,
  buatStatusTitik,
  konfirmasiTitikPending,
  bolehTerapkanHasilGps,
  opsiGpsSegar,
  pilihTitikGpsAktif,
  simpanTitikPending,
  selaraskanTitikTerkonfirmasi,
  type SumberTitik,
} from "./titikPending";

const TERKONFIRMASI = { lat: -6.9, lng: 107.6 };
const PENDING = { lat: -6.8, lng: 107.7 };

describe("status titik pending", () => {
  it.each<SumberTitik>(["PETA", "GPS", "GESER", "WILAYAH"])(
    "menyimpan kandidat dari sumber %s tanpa mengubah titik terkonfirmasi",
    (sumber) => {
      const hasil = simpanTitikPending(buatStatusTitik(TERKONFIRMASI), PENDING, sumber);
      expect(hasil).toEqual({
        terkonfirmasi: TERKONFIRMASI,
        pending: { titik: PENDING, sumber },
      });
    },
  );

  it("mengonfirmasi kandidat lalu membersihkan pending", () => {
    const status = simpanTitikPending(buatStatusTitik(TERKONFIRMASI), PENDING, "PETA");
    expect(konfirmasiTitikPending(status)).toEqual({
      status: { terkonfirmasi: { ...PENDING, sumber: "PETA" }, pending: null },
      titik: { ...PENDING, sumber: "PETA" },
    });
    expect(konfirmasiTitikPending(buatStatusTitik(TERKONFIRMASI))).toBeNull();
  });

  it("selalu meminta pembacaan GPS segar", () => {
    expect(opsiGpsSegar()).toEqual({
      enableHighAccuracy: true,
      timeout: 8000,
      maximumAge: 0,
    });
  });

  it("membawa akurasi dan sumber GPS ke titik terkonfirmasi", () => {
    const status = simpanTitikPending(
      buatStatusTitik(TERKONFIRMASI),
      { ...PENDING, akurasi_meter: 37.4 },
      "GPS",
    );
    expect(konfirmasiTitikPending(status)?.titik).toEqual({
      ...PENDING,
      akurasi_meter: 37.4,
      sumber: "GPS",
    });
  });

  it("tidak membawa akurasi GPS lama saat titik dipilih dari peta", () => {
    const status = simpanTitikPending(
      buatStatusTitik({ ...TERKONFIRMASI, akurasi_meter: 25, sumber: "GPS" }),
      PENDING,
      "PETA",
    );
    expect(konfirmasiTitikPending(status)?.titik).toEqual({ ...PENDING, sumber: "PETA" });
  });

  it.each<SumberTitik>(["PETA", "GESER", "WILAYAH"])(
    "tidak menampilkan akurasi GPS terkonfirmasi saat kandidat aktif berasal dari %s",
    (sumber) => {
      const gpsTerkonfirmasi = { ...TERKONFIRMASI, akurasi_meter: 25, sumber: "GPS" as const };
      const pending = { titik: PENDING, sumber };
      expect(pilihTitikGpsAktif(pending, gpsTerkonfirmasi)).toBeNull();
    },
  );

  it("menolak hasil GPS lama setelah ada permintaan atau pilihan lebih baru", () => {
    expect(bolehTerapkanHasilGps(2, 3)).toBe(false);
    expect(bolehTerapkanHasilGps(3, 3)).toBe(true);
  });

  it("membatalkan kandidat tanpa mengubah titik terkonfirmasi", () => {
    const status = simpanTitikPending(buatStatusTitik(TERKONFIRMASI), PENDING, "GPS");
    expect(batalkanTitikPending(status)).toEqual({ terkonfirmasi: TERKONFIRMASI, pending: null });
  });

  it("membersihkan kandidat saat titik terkonfirmasi berubah dari luar", () => {
    const status = simpanTitikPending(buatStatusTitik(TERKONFIRMASI), PENDING, "GESER");
    expect(selaraskanTitikTerkonfirmasi(status, { lat: -6.7, lng: 107.8 })).toEqual({
      terkonfirmasi: { lat: -6.7, lng: 107.8 },
      pending: null,
    });
  });

  it("mempertahankan kandidat saat titik terkonfirmasi tidak berubah", () => {
    const status = simpanTitikPending(buatStatusTitik(TERKONFIRMASI), PENDING, "WILAYAH");
    expect(selaraskanTitikTerkonfirmasi(status, TERKONFIRMASI)).toBe(status);
  });

  it("memblokir kelayakan saat titik tujuan masih pending", () => {
    const asal = buatStatusTitik(TERKONFIRMASI);
    const tujuan = simpanTitikPending(buatStatusTitik(TERKONFIRMASI), PENDING, "PETA");
    expect(adaTitikPending(asal, tujuan)).toBe(true);
  });

  it("memblokir kelayakan saat titik asal masih pending", () => {
    const asal = simpanTitikPending(buatStatusTitik(TERKONFIRMASI), PENDING, "GPS");
    const tujuan = buatStatusTitik(TERKONFIRMASI);
    expect(adaTitikPending(asal, tujuan)).toBe(true);
  });

  it("memulihkan kelayakan setelah kandidat dibatalkan", () => {
    const asalPending = simpanTitikPending(buatStatusTitik(TERKONFIRMASI), PENDING, "GESER");
    expect(adaTitikPending(batalkanTitikPending(asalPending), buatStatusTitik(TERKONFIRMASI))).toBe(false);
  });

  it("memulihkan kelayakan setelah kandidat dikonfirmasi", () => {
    const tujuanPending = simpanTitikPending(buatStatusTitik(TERKONFIRMASI), PENDING, "WILAYAH");
    const hasil = konfirmasiTitikPending(tujuanPending);
    if (!hasil) throw new Error("Kandidat seharusnya dapat dikonfirmasi");
    expect(adaTitikPending(buatStatusTitik(TERKONFIRMASI), hasil.status)).toBe(false);
  });
});
