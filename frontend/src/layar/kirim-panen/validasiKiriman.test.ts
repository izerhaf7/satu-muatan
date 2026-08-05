import { describe, expect, it } from "vitest";

import { daftarPenghambatKiriman, type KondisiKiriman } from "./validasiKiriman";

const KONDISI_VALID: KondisiKiriman = {
  komoditasId: "komoditas-1",
  volumeKg: 50,
  volumeMinimalKg: 50,
  tanggal: "2026-08-06",
  ringkasanTujuan: "Jl. Raya Cibiru, Bandung",
  adaTitikTujuan: true,
  tujuanPending: false,
  asalPending: false,
  alamatSedangDimuat: false,
  sedangMengirim: false,
};

function dengan(perubahan: Partial<KondisiKiriman>): KondisiKiriman {
  return { ...KONDISI_VALID, ...perubahan };
}

describe("daftarPenghambatKiriman", () => {
  it("meminta komoditas dipilih", () => {
    expect(daftarPenghambatKiriman(dengan({ komoditasId: "" }))).toContain(
      "Pilih komoditas yang akan dikirim.",
    );
  });

  it.each([Number.NaN, 0])("meminta volume diisi dengan angka positif untuk nilai %s", (volumeKg) => {
    expect(daftarPenghambatKiriman(dengan({ volumeKg }))).toContain(
      "Isi volume dengan angka lebih dari 0 kg.",
    );
  });

  it("menjelaskan volume yang masih di bawah minimum server", () => {
    expect(daftarPenghambatKiriman(dengan({ volumeKg: 49 }))).toContain(
      "Tambah volume menjadi minimal 50 kg.",
    );
  });

  it("meminta tanggal siap diisi", () => {
    expect(daftarPenghambatKiriman(dengan({ tanggal: "" }))).toContain("Pilih tanggal siap panen.");
  });

  it("meminta alamat tujuan dilengkapi saat ringkasan kosong", () => {
    expect(daftarPenghambatKiriman(dengan({ ringkasanTujuan: "   " }))).toContain(
      "Lengkapi alamat tujuan pengiriman.",
    );
  });

  it("meminta titik tujuan ditandai", () => {
    expect(daftarPenghambatKiriman(dengan({ adaTitikTujuan: false }))).toContain(
      "Tandai titik tujuan di peta.",
    );
  });

  it("meminta kandidat titik tujuan dikonfirmasi atau dibatalkan", () => {
    expect(daftarPenghambatKiriman(dengan({ tujuanPending: true }))).toContain(
      "Konfirmasi atau batalkan titik tujuan yang baru.",
    );
  });

  it("meminta kandidat titik asal dikonfirmasi atau dibatalkan", () => {
    expect(daftarPenghambatKiriman(dengan({ asalPending: true }))).toContain(
      "Konfirmasi atau batalkan titik penjemputan yang baru.",
    );
  });

  it("meminta pengguna menunggu pembacaan alamat", () => {
    expect(daftarPenghambatKiriman(dengan({ alamatSedangDimuat: true }))).toContain(
      "Tunggu sampai alamat dari peta selesai dibaca.",
    );
  });

  it("mempertahankan pengiriman yang sedang diproses sebagai penghambat", () => {
    expect(daftarPenghambatKiriman(dengan({ sedangMengirim: true }))).toContain(
      "Tunggu sampai pengiriman sebelumnya selesai diproses.",
    );
  });

  it("tidak menghambat kondisi valid dengan titik asal kosong", () => {
    expect(daftarPenghambatKiriman(KONDISI_VALID)).toEqual([]);
  });
});
