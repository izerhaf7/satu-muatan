import { describe, expect, it, vi } from "vitest";

const queryOptions = vi.hoisted(() => vi.fn((options: unknown) => options));

vi.mock("@tanstack/react-query", () => ({ useQuery: queryOptions }));

import {
  buatPilihanWilayah,
  buatPathWilayahAnak,
  cariKodeWilayah,
  gantiWilayahDariGeokode,
  isiKodePosOtomatis,
  pilihWilayah,
  resetKodePosOtomatis,
  resetTurunanWilayah,
  kodeWilayahAktif,
  tingkatAnak,
  ubahKodePosManual,
  type NilaiWilayahCascade,
} from "./wilayahCascade";
import { useCariWilayahAnak } from "@/hooks/useAlamat";
import { terapkanGeokode, terapkanWilayah, type NilaiAlamat } from "./FormAlamat";

const TERISI: NilaiWilayahCascade = {
  provinsi: "Jawa Barat",
  provinsiKode: "32",
  kabupaten: "Kabupaten Garut",
  kabupatenKode: "32.05",
  kecamatan: "Cikajang",
  kecamatanKode: "32.05.22",
  desa: "Cikajang",
  desaKode: "32.05.22.2001",
  kode_pos: "44171",
};

describe("tingkatAnak", () => {
  it.each([
    ["PROVINSI", "KABUPATEN"],
    ["KABUPATEN", "KECAMATAN"],
    ["KECAMATAN", "DESA"],
    ["DESA", null],
  ] as const)("mengembalikan tingkat setelah %s", (tingkat, hasil) => {
    expect(tingkatAnak(tingkat)).toBe(hasil);
  });
});

describe("buatPathWilayahAnak", () => {
  it("membuat query provinsi tanpa induk", () => {
    expect(buatPathWilayahAnak("PROVINSI")).toBe("/api/wilayah/anak?tingkat=PROVINSI");
  });

  it("menambahkan induk terenkode hanya saat tersedia", () => {
    expect(buatPathWilayahAnak("KECAMATAN", "32.05/Barat")).toBe(
      "/api/wilayah/anak?tingkat=KECAMATAN&induk_kode=32.05%2FBarat",
    );
  });
});

describe("cariKodeWilayah", () => {
  it("mencocokkan nama reverse geocode tanpa awalan administratif", () => {
    const daftar = [
      {
        kode: "32.01",
        nama: "Kabupaten Bogor",
        tingkat: "KABUPATEN" as const,
        jalur: "Kabupaten Bogor, Jawa Barat",
        kode_pos: null,
        lat: null,
        lng: null,
        induk_kode: "32",
      },
    ];

    expect(cariKodeWilayah("Bogor", daftar)).toBe("32.01");
    expect(cariKodeWilayah("Kabupaten Bogor", daftar)).toBe("32.01");
  });
});

describe("useCariWilayahAnak", () => {
  it("mengaktifkan provinsi tanpa induk dengan cache sepuluh menit", () => {
    useCariWilayahAnak("PROVINSI");

    expect(queryOptions).toHaveBeenLastCalledWith(
      expect.objectContaining({
        queryKey: ["wilayah-anak", "PROVINSI", null],
        enabled: true,
        staleTime: 10 * 60 * 1000,
      }),
    );
  });

  it("menonaktifkan tingkat bawah sampai induk tersedia", () => {
    useCariWilayahAnak("DESA", null);

    expect(queryOptions).toHaveBeenLastCalledWith(
      expect.objectContaining({
        queryKey: ["wilayah-anak", "DESA", null],
        enabled: false,
      }),
    );
  });
});

describe("resetTurunanWilayah", () => {
  it("mengganti provinsi dan membersihkan semua turunannya", () => {
    expect(resetTurunanWilayah(TERISI, "PROVINSI", "Banten", "36")).toEqual({
      provinsi: "Banten",
      provinsiKode: "36",
      kabupaten: null,
      kabupatenKode: null,
      kecamatan: null,
      kecamatanKode: null,
      desa: null,
      desaKode: null,
      kode_pos: "44171",
    });
  });

  it("mengganti kabupaten dan hanya membersihkan tingkat di bawahnya", () => {
    expect(resetTurunanWilayah(TERISI, "KABUPATEN", "Kabupaten Bandung", "32.04")).toEqual({
      ...TERISI,
      kabupaten: "Kabupaten Bandung",
      kabupatenKode: "32.04",
      kecamatan: null,
      kecamatanKode: null,
      desa: null,
      desaKode: null,
      kode_pos: "44171",
    });
  });

  it("mengganti kecamatan dan hanya membersihkan desa", () => {
    expect(resetTurunanWilayah(TERISI, "KECAMATAN", "Tarogong Kidul", "32.05.31")).toEqual({
      ...TERISI,
      kecamatan: "Tarogong Kidul",
      kecamatanKode: "32.05.31",
      desa: null,
      desaKode: null,
      kode_pos: "44171",
    });
  });

  it("mempertahankan kode pos manual saat induk berubah", () => {
    expect(resetTurunanWilayah(TERISI, "PROVINSI", "Banten", "36").kode_pos).toBe("44171");
  });
});

describe("pilihWilayah", () => {
  const desa = {
    kode: "32.05.22.2002",
    nama: "Mekarjaya",
    tingkat: "DESA" as const,
    jalur: "Mekarjaya, Cikajang, Kabupaten Garut, Jawa Barat",
    kode_pos: "44171",
    lat: null,
    lng: null,
    induk_kode: "32.05.22",
  };

  it("mengisi kode pos desa saat kode pos sekarang kosong", () => {
    expect(pilihWilayah({ ...TERISI, kode_pos: null }, desa)).toMatchObject({
      desa: "Mekarjaya",
      desaKode: "32.05.22.2002",
      kode_pos: "44171",
    });
  });

  it("mempertahankan kode pos yang sudah diisi manual", () => {
    expect(pilihWilayah({ ...TERISI, kode_pos: "40123" }, desa).kode_pos).toBe("40123");
  });
});

describe("provenance kode pos otomatis", () => {
  it.each(["PROVINSI", "KABUPATEN", "KECAMATAN"] as const)(
    "membersihkan kode pos otomatis saat %s berubah",
    () => {
      expect(resetKodePosOtomatis("44171", "44171")).toEqual({ nilai: null, otomatis: null });
    },
  );

  it("mempertahankan kode pos manual yang sama dengan nilai otomatis lama", () => {
    expect(resetKodePosOtomatis("44171", null)).toEqual({ nilai: "44171", otomatis: null });
  });

  it("mempertahankan kode pos manual yang berbeda", () => {
    expect(resetKodePosOtomatis("40123", null)).toEqual({ nilai: "40123", otomatis: null });
  });

  it("mempertahankan edit manual setelah kode pos pernah terisi otomatis", () => {
    const setelahEditManual = ubahKodePosManual("40200");
    expect(resetKodePosOtomatis(setelahEditManual.nilai, setelahEditManual.otomatis)).toEqual(setelahEditManual);
  });

  it("mengisi dan menandai kode pos dari Desa setelah kode pos dibersihkan", () => {
    const setelahReset = resetKodePosOtomatis("44171", "44171");
    expect(isiKodePosOtomatis(setelahReset.nilai, "40374")).toEqual({
      nilai: "40374",
      otomatis: "40374",
    });
  });

  it("tidak menandai kode pos otomatis ketika nilai manual sudah ada", () => {
    expect(isiKodePosOtomatis("40123", "44171")).toEqual({ nilai: "40123", otomatis: null });
  });
});

describe("gantiWilayahDariGeokode", () => {
  it("mengganti nama lama untuk semua hasil geokode non-null", () => {
    expect(
      gantiWilayahDariGeokode(TERISI, {
        desa: "Sukamaju",
        kecamatan: "Cimaung",
        kabupaten: "Kabupaten Bandung",
        provinsi: "Jawa Barat",
        kode_pos: "40374",
      }),
    ).toEqual({
      ...TERISI,
      desa: "Sukamaju",
      kecamatan: "Cimaung",
      kabupaten: "Kabupaten Bandung",
      provinsi: "Jawa Barat",
      kode_pos: "40374",
      provinsiKode: null,
      kabupatenKode: null,
      kecamatanKode: null,
      desaKode: null,
    });
  });

  it("mempertahankan nama lama saat hasil geokode null", () => {
    expect(
      gantiWilayahDariGeokode(TERISI, {
        desa: null,
        kecamatan: "Cimaung",
        kabupaten: null,
        provinsi: null,
        kode_pos: null,
      }),
    ).toEqual({
      ...TERISI,
      kecamatan: "Cimaung",
      kecamatanKode: null,
    });
  });
});

describe("rekonsiliasi pilihan wilayah", () => {
  const opsi = [
    {
      kode: "32",
      nama: "Jawa Barat",
      tingkat: "PROVINSI" as const,
      jalur: "Jawa Barat",
      kode_pos: null,
      lat: null,
      lng: null,
      induk_kode: null,
    },
  ];

  it("mencocokkan nama tanpa membedakan kapitalisasi atau spasi", () => {
    expect(cariKodeWilayah("  jawa BARAT ", opsi)).toBe("32");
  });

  it("menampilkan nama geokode yang belum cocok sebagai pilihan sementara", () => {
    expect(buatPilihanWilayah("Banten", opsi)).toEqual([
      { kode: "Banten", nama: "Banten", sementara: true },
      { kode: "32", nama: "Jawa Barat", sementara: false },
    ]);
  });

  it("tidak menggandakan pilihan sementara setelah nama cocok", () => {
    expect(buatPilihanWilayah("jawa barat", opsi)).toEqual([
      { kode: "32", nama: "Jawa Barat", sementara: false },
    ]);
  });

  it("mempertahankan kode lokal selama opsi nama yang sama masih dimuat", () => {
    expect(kodeWilayahAktif("Jawa Barat", { kode: "32", nama: "jawa barat" }, undefined)).toBe("32");
  });

  it("membuang kode lokal lama saat geokode mengganti nama", () => {
    expect(kodeWilayahAktif("Banten", { kode: "32", nama: "Jawa Barat" }, undefined)).toBeNull();
  });

  it("memakai kode kanonis dari opsi setelah opsi termuat", () => {
    expect(kodeWilayahAktif("jawa barat", { kode: "lama", nama: "Jawa Barat" }, opsi)).toBe("32");
  });
});

describe("terapkanGeokode", () => {
  const alamat: NilaiAlamat = {
    alamat: "Alamat manual",
    nama: "Bu Rina",
    telepon: "081200000021",
    jalan: "Jl. Lama 1",
    rt_rw: "001/002",
    desa: "Desa Lama",
    kecamatan: "Kecamatan Lama",
    kabupaten: "Kabupaten Lama",
    provinsi: "Provinsi Lama",
    kode_pos: "40123",
    patokan: "Pagar hijau",
  };

  it("mengganti hirarki non-null dan mempertahankan field manual lain", () => {
    expect(
      terapkanGeokode(alamat, {
        alamat: "Alamat geokode",
        desa: "Desa Baru",
        kecamatan: "Kecamatan Baru",
        kabupaten: "Kabupaten Baru",
        provinsi: "Provinsi Baru",
        kode_pos: "44171",
        sumber: "LOKAL",
      }),
    ).toEqual({
      ...alamat,
      desa: "Desa Baru",
      kecamatan: "Kecamatan Baru",
      kabupaten: "Kabupaten Baru",
      provinsi: "Provinsi Baru",
    });
  });

  it("mempertahankan hirarki lama untuk field geokode null", () => {
    expect(
      terapkanGeokode(alamat, {
        alamat: "Alamat geokode",
        desa: null,
        kecamatan: "Kecamatan Baru",
        kabupaten: null,
        provinsi: null,
        kode_pos: null,
        sumber: "LOKAL",
      }),
    ).toMatchObject({
      desa: "Desa Lama",
      kecamatan: "Kecamatan Baru",
      kabupaten: "Kabupaten Lama",
      provinsi: "Provinsi Lama",
      kode_pos: "40123",
    });
  });
});

describe("terapkanWilayah", () => {
  it("mempertahankan kode pos manual saat wilayah memiliki kode pos", () => {
    const alamat = {
      alamat: "Alamat manual",
      kode_pos: "40123",
    } as NilaiAlamat;

    expect(
      terapkanWilayah(alamat, {
        kode: "32.05.22.2001",
        nama: "Cikajang",
        tingkat: "DESA",
        jalur: "Cikajang, Cikajang, Kabupaten Garut, Jawa Barat",
        kode_pos: "44171",
        lat: null,
        lng: null,
      }).kode_pos,
    ).toBe("40123");
  });
});
