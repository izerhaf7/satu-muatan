import { describe, expect, it } from "vitest";

import {
  BATAS_KARAKTER_POLYLINE,
  BATAS_TITIK_POLYLINE,
  decodePolyline,
  interpolasiKoordinat,
  pilihRuteTampil,
  proyeksikanKeRute,
} from "./geometriRute";

const RUTE_CONTOH = "_p~iF~ps|U_ulLnnqC_mqNvxq`@";

describe("decodePolyline", () => {
  it("menerbitkan batas keamanan decoder", () => {
    expect(BATAS_KARAKTER_POLYLINE).toBe(100_000);
    expect(BATAS_TITIK_POLYLINE).toBe(10_000);
  });

  it("mendekode polyline Google standar", () => {
    expect(decodePolyline(RUTE_CONTOH)).toEqual([
      { lat: 38.5, lng: -120.2 },
      { lat: 40.7, lng: -120.95 },
      { lat: 43.252, lng: -126.453 },
    ]);
  });

  it.each([null, "", "?", "_p~iF~ps|U", "~~~~~~"]) (
    "menolak polyline null, tidak lengkap, atau kurang dari dua titik: %s",
    (encoded) => {
      expect(decodePolyline(encoded)).toBeNull();
    },
  );

  it("menolak encoded polyline di atas batas karakter", () => {
    expect(decodePolyline("??".repeat(50_001))).toBeNull();
  });

  it("menolak path valid di atas batas jumlah titik", () => {
    expect(decodePolyline("??".repeat(10_001))).toBeNull();
  });
});

describe("pilihRuteTampil", () => {
  const fallback = [
    { lat: -6.9, lng: 107.6 },
    { lat: -6.8, lng: 107.7 },
  ];

  it("memakai rute provider yang valid", () => {
    expect(pilihRuteTampil(RUTE_CONTOH, fallback)).toEqual(decodePolyline(RUTE_CONTOH));
  });

  it("mempertahankan garis lurus lama saat rute tidak valid", () => {
    expect(pilihRuteTampil("rusak", fallback)).toBe(fallback);
  });
});

describe("proyeksikanKeRute", () => {
  it("memproyeksikan posisi ke segmen geografis terdekat", () => {
    const hasil = proyeksikanKeRute(
      { lat: -6.95, lng: 107.7 },
      [
        { lat: -7, lng: 107.6 },
        { lat: -7, lng: 107.8 },
      ],
    );

    expect(hasil.lat).toBeCloseTo(-7, 5);
    expect(hasil.lng).toBeCloseTo(107.7, 5);
  });

  it("mengembalikan posisi asli jika rute tidak valid", () => {
    const posisi = { lat: -6.95, lng: 107.7 };
    expect(proyeksikanKeRute(posisi, [posisi])).toBe(posisi);
  });
});

describe("interpolasiKoordinat", () => {
  it("melanjutkan gerak dari koordinat yang sedang ditampilkan", () => {
    const sedangTampil = { lat: -6.95, lng: 107.65 };
    const targetBaru = { lat: -6.85, lng: 107.75 };

    expect(interpolasiKoordinat(sedangTampil, targetBaru, 0)).toEqual(sedangTampil);
    expect(interpolasiKoordinat(sedangTampil, targetBaru, 0.5)).toEqual({ lat: -6.9, lng: 107.7 });
    expect(interpolasiKoordinat(sedangTampil, targetBaru, 1)).toEqual(targetBaru);
  });
});
