/** Layar Serah Terima (§9.7, peran Penerima) — pilih dari daftar lot masuk (jalur utama)
 *  atau input manual kode QR, lalu putuskan Terima / Terima dengan potongan / Tolak.
 *  Guard peran PENERIMA sudah terpusat di RuteDenganPeran (App.tsx). */

import { type FormEvent, useState } from "react";
import { AlertTriangle, ArrowLeft, ScanLine } from "lucide-react";

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import InputTeks from "@/komponen/InputTeks";
import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { SkeletonKartu } from "@/komponen/Skeleton";
import Tombol from "@/komponen/Tombol";
import { LABEL_GRADE } from "@/komponen/PilihGrade";
import type { components } from "@/api/client";
import { useCariLotQr, useKirimSerahTerima, useLotMasuk } from "@/hooks/useSerahTerima";
import { formatAngka } from "@/utils/format";

import KartuBukti from "./serah-terima/KartuBukti";

type BuktiLotOut = components["schemas"]["BuktiLotOut"];

export default function SerahTerima() {
  const [kodeQr, setKodeQr] = useState("");
  const [buktiTerpilih, setBuktiTerpilih] = useState<BuktiLotOut | null>(null);

  const lotMasuk = useLotMasuk();
  const cariQr = useCariLotQr();
  const kirim = useKirimSerahTerima();

  function cariBerdasarkanKode(e: FormEvent) {
    e.preventDefault();
    const kode = kodeQr.trim();
    if (!kode) return;
    cariQr.mutate(kode, { onSuccess: (data) => setBuktiTerpilih(data) });
  }

  if (buktiTerpilih) {
    return (
      <div className="flex flex-col gap-4 lg:mx-auto lg:w-full lg:max-w-3xl">
        <HeaderLayar judul="Serah Terima" />
        <Tombol
          type="button"
          varian="halus"
          ikon={ArrowLeft}
          className="w-fit px-3"
          onClick={() => {
            setBuktiTerpilih(null);
            setKodeQr("");
          }}
        >
          Kembali ke daftar
        </Tombol>

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
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 lg:grid lg:grid-cols-2 lg:items-start">
      <div className="lg:col-span-2">
        <HeaderLayar judul="Serah Terima" subjudul="Pilih lot yang sampai, atau masukkan kode QR-nya" />
      </div>

      <form onSubmit={cariBerdasarkanKode} className="kartu-datar flex flex-col gap-3 p-4">
        <InputTeks
          label="Kode QR lot"
          name="kode_qr"
          value={kodeQr}
          onChange={(e) => setKodeQr(e.target.value)}
          placeholder="mis. LOT-SM-20260805-CKJ-01-01"
        />
        {cariQr.isError && (
          <p role="alert" className="text-keterangan text-tanah-liat">
            Lot dengan kode itu tidak ditemukan, atau bukan untuk Anda.
          </p>
        )}
        <Tombol
          type="submit"
          varian="sekunder"
          ikon={ScanLine}
          sedangProses={cariQr.isPending}
          disabled={!kodeQr.trim()}
        >
          Cari kode QR
        </Tombol>
      </form>

      <section aria-label="Lot masuk" className="flex flex-col gap-3">
        <p className="text-base font-semibold text-tanah">Lot masuk</p>
        {lotMasuk.isLoading && <SkeletonKartu jumlah={3} />}
        {lotMasuk.isError && <KartuGalat pesan="Gagal memuat daftar lot." onCobaLagi={() => lotMasuk.refetch()} />}
        {lotMasuk.data?.length === 0 && (
          <KeadaanKosong pesan="Belum ada lot yang sampai untuk diserahterimakan. Lot akan muncul di sini begitu kiriman tiba." />
        )}
        {lotMasuk.data?.map((bukti) => (
          <button
            key={bukti.lot.id}
            type="button"
            onClick={() => setBuktiTerpilih(bukti)}
            className="kartu-datar flex flex-col gap-1.5 p-4 text-left transition-colors duration-cepat hover:border-daun focus-visible:border-daun"
          >
            <div className="flex items-center justify-between gap-2">
              <p className="text-base font-semibold text-tanah">{bukti.lot.nama_petani}</p>
              {bukti.lot.grade_asal < 3 && (
                <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-tanah-liat/10 px-2.5 py-0.5 text-keterangan font-semibold text-tanah-liat">
                  <AlertTriangle aria-hidden className="h-3.5 w-3.5" />
                  Grade {LABEL_GRADE[bukti.lot.grade_asal]}
                </span>
              )}
            </div>
            <p className="text-keterangan text-tanah/70">
              {bukti.lot.nama_komoditas}
              {bukti.lot.berat_aktual_kg !== null && bukti.lot.berat_aktual_kg !== undefined && (
                <>
                  {" · "}
                  <span className="angka">{formatAngka(bukti.lot.berat_aktual_kg)} kg</span>
                </>
              )}
            </p>
            <p className="angka text-keterangan text-tanah/50">{bukti.lot.kode_qr}</p>
          </button>
        ))}
      </section>
    </div>
  );
}
