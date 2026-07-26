/** Layar Serah Terima (§9.7, peran Penerima) — pilih dari daftar lot masuk (jalur utama)
 *  atau input manual kode QR, lalu putuskan Terima / Terima dengan potongan / Tolak. */

import { type FormEvent, useState } from "react";

import InputTeks from "@/komponen/InputTeks";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import Tombol from "@/komponen/Tombol";
import type { components } from "@/api/client";
import { useCariLotQr, useKirimSerahTerima, useLotMasuk } from "@/hooks/useSerahTerima";
import { useAuthStore } from "@/stores/authStore";
import { formatAngka } from "@/utils/format";

import KartuBukti from "./serah-terima/KartuBukti";

type BuktiLotOut = components["schemas"]["BuktiLotOut"];

export default function SerahTerima() {
  const pengguna = useAuthStore((s) => s.pengguna);

  const [kodeQr, setKodeQr] = useState("");
  const [buktiTerpilih, setBuktiTerpilih] = useState<BuktiLotOut | null>(null);

  const lotMasuk = useLotMasuk();
  const cariQr = useCariLotQr();
  const kirim = useKirimSerahTerima();

  if (pengguna?.peran !== "PENERIMA") {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6">
        <h1 className="text-2xl font-bold text-tanah">Serah Terima</h1>
        <KeadaanKosong pesan="Halaman ini khusus dapur penerima." teksAksi="Kembali ke Beranda" ke="/" />
      </main>
    );
  }

  function cariBerdasarkanKode(e: FormEvent) {
    e.preventDefault();
    const kode = kodeQr.trim();
    if (!kode) return;
    cariQr.mutate(kode, { onSuccess: (data) => setBuktiTerpilih(data) });
  }

  if (buktiTerpilih) {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6 pb-24">
        <header className="flex flex-col gap-3">
          <button
            type="button"
            onClick={() => {
              setBuktiTerpilih(null);
              setKodeQr("");
            }}
            className="inline-flex min-h-sentuh w-fit items-center gap-1 text-base font-medium text-tanah"
          >
            ← Kembali ke daftar
          </button>
          <h1 className="text-2xl font-bold text-tanah">Serah Terima</h1>
        </header>

        <KartuBukti
          bukti={buktiTerpilih}
          sedangMengirim={kirim.isPending}
          gagalMengirim={kirim.isError}
          onKirim={(body) =>
            kirim.mutate(
              { lotId: buktiTerpilih.lot.id, body },
              { onSuccess: (data) => setBuktiTerpilih({ ...buktiTerpilih, serah_terima: data }) },
            )
          }
        />
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6 pb-24">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-tanah">Serah Terima</h1>
        <p className="text-base text-tanah/70">Pilih lot yang sampai, atau masukkan kode QR-nya</p>
      </header>

      <form onSubmit={cariBerdasarkanKode} className="flex flex-col gap-3 rounded-lg border-2 border-kabut p-4">
        <InputTeks
          label="Kode QR lot"
          name="kode_qr"
          value={kodeQr}
          onChange={(e) => setKodeQr(e.target.value)}
          placeholder="mis. LOT-SM-20260805-CKJ-01-01"
        />
        {cariQr.isError && (
          <p role="alert" className="text-sm text-tanah-liat">
            Lot dengan kode itu tidak ditemukan, atau bukan untuk Anda.
          </p>
        )}
        <Tombol type="submit" varian="sekunder" disabled={!kodeQr.trim() || cariQr.isPending}>
          {cariQr.isPending ? "Mencari…" : "Cari kode QR"}
        </Tombol>
      </form>

      <section aria-label="Lot masuk" className="flex flex-col gap-3">
        <p className="text-base font-semibold text-tanah">Lot masuk</p>
        {lotMasuk.isLoading && <p className="text-base text-tanah/60">Memuat daftar lot…</p>}
        {lotMasuk.isError && (
          <div className="flex flex-col items-start gap-3 rounded-lg border-2 border-tanah-liat/40 p-4">
            <p className="text-base text-tanah-liat">Gagal memuat daftar lot.</p>
            <Tombol varian="sekunder" onClick={() => lotMasuk.refetch()}>
              Coba lagi
            </Tombol>
          </div>
        )}
        {lotMasuk.data?.length === 0 && (
          <KeadaanKosong pesan="Belum ada lot yang sampai untuk diserahterimakan. Lot akan muncul di sini begitu kiriman tiba." />
        )}
        {lotMasuk.data?.map((bukti) => (
          <button
            key={bukti.lot.id}
            type="button"
            onClick={() => setBuktiTerpilih(bukti)}
            className="flex min-h-sentuh flex-col gap-1 rounded-lg border-2 border-kabut p-4 text-left hover:border-daun focus-visible:border-daun"
          >
            <div className="flex items-center justify-between gap-2">
              <p className="text-base font-semibold text-tanah">{bukti.lot.nama_petani}</p>
              {bukti.lot.cacat_terlihat && (
                <span className="rounded-full border-2 border-tanah-liat px-2 py-0.5 text-sm font-medium text-tanah-liat">
                  Cacat terlihat
                </span>
              )}
            </div>
            <p className="text-sm text-tanah/70">
              {bukti.lot.nama_komoditas}
              {bukti.lot.berat_aktual_kg !== null && bukti.lot.berat_aktual_kg !== undefined
                ? ` · ${formatAngka(bukti.lot.berat_aktual_kg)} kg`
                : ""}
            </p>
            <p className="angka text-sm text-tanah/50">{bukti.lot.kode_qr}</p>
          </button>
        ))}
      </section>
    </main>
  );
}
