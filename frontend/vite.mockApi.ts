// MOCK DEV FASE 1 — server dev-only, TIDAK dipakai produksi/build.
// Aktif hanya saat `VITE_MOCK=1 npm run dev`. Tujuan: verifikasi visual layar
// selagi backend sungguhan (worktree paralel) masih 501. Data di sini murni
// contoh tampilan lokal, bukan sumber kebenaran — sumber kebenaran tetap
// kontrak/openapi.yaml + mesin backend asli.
//
// Angka dipakai mengikuti KEPUTUSAN.md K2 (rute Cikajang -> 3 dapur Bandung,
// 70,03 km) supaya tidak menyesatkan siapa pun yang membaca kode ini.

import type { Connect, Plugin } from "vite";

function baca(req: Connect.IncomingMessage): Promise<unknown> {
  return new Promise((resolve) => {
    let raw = "";
    req.on("data", (chunk) => (raw += chunk));
    req.on("end", () => {
      try {
        resolve(raw ? JSON.parse(raw) : null);
      } catch {
        resolve(null);
      }
    });
  });
}

function kirim(res: Connect.OutgoingMessage & { statusCode?: number }, status: number, body: unknown) {
  res.statusCode = status;
  res.setHeader("Content-Type", "application/json");
  res.end(JSON.stringify(body));
}

const AKUN_DEMO: Record<string, { id: string; nama: string; no_hp: string; peran: string; koperasi_id?: string; penerima_id?: string }> = {
  KOPERASI: { id: "u-koperasi", nama: "Bu Nia", no_hp: "081200000001", peran: "KOPERASI", koperasi_id: "kop-1" },
  PETANI_ASEP: { id: "u-asep", nama: "Asep", no_hp: "081200000011", peran: "PETANI", koperasi_id: "kop-1" },
  PETANI_WATI: { id: "u-wati", nama: "Wati", no_hp: "081200000012", peran: "PETANI", koperasi_id: "kop-1" },
  PETANI_DEDI: { id: "u-dedi", nama: "Dedi", no_hp: "081200000013", peran: "PETANI", koperasi_id: "kop-1" },
  PETANI_IJAH: { id: "u-ijah", nama: "Ijah", no_hp: "081200000014", peran: "PETANI", koperasi_id: "kop-1" },
  PENERIMA_CIBIRU: { id: "u-rina", nama: "Bu Rina", no_hp: "081200000021", peran: "PENERIMA", penerima_id: "pnr-cibiru" },
};

const PENERIMA = [
  { id: "pnr-panyileukan", nama: "SPPG Panyileukan 2", tipe: "SPPG", alamat: "Panyileukan, Bandung", lat: -6.9333, lng: 107.6989 },
  { id: "pnr-ujungberung", nama: "SPPG Ujungberung 1", tipe: "SPPG", alamat: "Ujungberung, Bandung", lat: -6.9147, lng: 107.7 },
  { id: "pnr-cibiru", nama: "SPPG Cibiru 3", tipe: "SPPG", alamat: "Cibiru, Bandung", lat: -6.9269, lng: 107.7189 },
];

const KOMODITAS = [
  { id: "kom-kubis", nama: "Kubis", satuan: "kg", harga_acuan_per_kg: 3000, umur_simpan_jam: 168, laju_susut_per_jam: 0.0025, status_sumber: "ASUMSI", catatan_sumber: "Perkiraan, ganti data PIHPS sebelum final." },
  { id: "kom-tomat", nama: "Tomat", satuan: "kg", harga_acuan_per_kg: 5000, umur_simpan_jam: 96, laju_susut_per_jam: 0.0052, status_sumber: "ASUMSI", catatan_sumber: "Perkiraan, ganti data PIHPS sebelum final." },
];

function slotDibuka() {
  const cutoff = new Date(Date.now() + 2 * 60 * 60 * 1000 + 14 * 60 * 1000).toISOString();
  return {
    id: "slot-1",
    kode: "SM-20260805-CKJ-01",
    tanggal_kirim: "2026-08-05",
    cutoff_at: cutoff,
    status: "DIBUKA",
    jarak_km: 70.03,
    volume_terkunci_kg: 780,
    kapasitas_rencana_kg: 2000,
    tier_ringkas: "VAN",
    jumlah_petani: 4,
  };
}

function slotSelesai() {
  return {
    id: "slot-0",
    kode: "SM-20260715-CKJ-01",
    tanggal_kirim: "2026-07-15",
    cutoff_at: "2026-07-15T06:00:00Z",
    status: "SELESAI",
    jarak_km: 70.03,
    volume_terkunci_kg: 1450,
    kapasitas_rencana_kg: 2000,
    tier_ringkas: "VAN",
    jumlah_petani: 5,
  };
}

/** MOCK DEV FASE 1 — plugin Vite, aktif hanya saat VITE_MOCK=1. */
export function mockApiPlugin(): Plugin {
  return {
    name: "mock-api-fase1",
    configureServer(server) {
      server.middlewares.use(async (req, res, next) => {
        const url = req.url ?? "";
        if (!url.startsWith("/api/")) return next();

        const [path] = url.split("?");
        const method = (req.method ?? "GET").toUpperCase();

        if (path === "/api/auth/masuk-demo" && method === "POST") {
          const body = (await baca(req)) as { akun?: string } | null;
          const akun = body?.akun ? AKUN_DEMO[body.akun] : undefined;
          if (!akun) return kirim(res, 422, { detail: [{ loc: ["body", "akun"], msg: "akun tidak dikenal", type: "value_error", input: body }] });
          return kirim(res, 200, { token: `mock-token-${akun.id}`, pengguna: akun });
        }

        if (path === "/api/auth/masuk" && method === "POST") {
          return kirim(res, 200, { token: "mock-token-u-koperasi", pengguna: AKUN_DEMO.KOPERASI });
        }

        if (path === "/api/auth/saya" && method === "GET") {
          return kirim(res, 200, AKUN_DEMO.KOPERASI);
        }

        if (path === "/api/penerima" && method === "GET") {
          return kirim(res, 200, PENERIMA);
        }

        if (path === "/api/komoditas" && method === "GET") {
          return kirim(res, 200, KOMODITAS);
        }

        if (path === "/api/slot" && method === "GET") {
          const status = new URLSearchParams(url.split("?")[1] ?? "").get("status");
          const semua = [slotDibuka(), slotSelesai()];
          return kirim(res, 200, status ? semua.filter((s) => s.status === status) : semua);
        }

        if (path === "/api/slot" && method === "POST") {
          const s = slotDibuka();
          return kirim(res, 201, { ...s, waktu_server: new Date().toISOString(), koperasi: { id: "kop-1", nama: "Koperasi Desa Mekarjaya", kode: "CKJ", alamat_gudang: "Cikajang, Garut", lat: -7.3661, lng: 107.7961 }, tujuan: [], partisipasi: [], subsidi_koperasi: 0 });
        }

        if (path === "/api/slot/pratinjau" && method === "POST") {
          const body = (await baca(req)) as { tujuan?: string[]; skenario_volume?: number[] } | null;
          const tujuanIds = body?.tujuan ?? [];
          const rute = tujuanIds.map((id, i) => {
            const p = PENERIMA.find((x) => x.id === id);
            return { urutan: i + 1, penerima_id: id, nama_penerima: p?.nama ?? id, jarak_segmen_km: 23.34 };
          });
          const volumes = body?.skenario_volume ?? [300, 800, 2000];
          // Angka K2 (rute 70,03 km): 300kg->1007, 800kg->415, 2000kg->~272 (ENGKEL, ilustratif).
          const tabel = volumes.map((v) => {
            if (v <= 300) return { volume_kg: v, harga_per_kg: 1007, biaya_total: 302077, kendaraan: ["VAN"] };
            if (v <= 800) return { volume_kg: v, harga_per_kg: 415, biaya_total: 332000, kendaraan: ["VAN"] };
            return { volume_kg: v, harga_per_kg: 272, biaya_total: 543000, kendaraan: ["ENGKEL"] };
          });
          return kirim(res, 200, { jarak_km: 70.03, rute, tabel_harga: tabel });
        }

        if (path === "/api/dampak/bulanan" && method === "GET") {
          const bulanIni = new Date();
          const kunci = `${bulanIni.getFullYear()}-${String(bulanIni.getMonth() + 1).padStart(2, "0")}`;
          return kirim(res, 200, [
            { bulan: kunci, jumlah_kiriman: 6, penghematan_rp: 3120000, truk_km_dihemat: 210, emisi_kg: 84.5, susut_kg: null },
          ]);
        }

        return next();
      });
    },
  };
}
