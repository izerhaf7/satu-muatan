/** Layar Muat (§9.5, peran Koperasi) — timbang tiap lot, foto, cacat terlihat, QR,
 *  lalu "Selesai muat" memberangkatkan slot (status -> JALAN). */

import { Link, useParams } from "react-router-dom";

import KeadaanKosong from "@/komponen/KeadaanKosong";
import Tombol from "@/komponen/Tombol";
import { useDaftarLotSlot, useMuatLot, useSelesaiMuat, useSlotUntukMuat } from "@/hooks/useLot";
import { useAuthStore } from "@/stores/authStore";

import KartuLotMuat from "./muat/KartuLotMuat";

export default function Muat() {
  const { id: slotId } = useParams();
  const pengguna = useAuthStore((s) => s.pengguna);

  const slot = useSlotUntukMuat(slotId);
  const daftarLot = useDaftarLotSlot(slotId);
  const muatLot = useMuatLot(slotId);
  const selesaiMuat = useSelesaiMuat(slotId);

  if (pengguna?.peran !== "KOPERASI") {
    return (
      <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6">
        <h1 className="text-2xl font-bold text-tanah">Muat</h1>
        <KeadaanKosong pesan="Halaman ini khusus pengurus koperasi." teksAksi="Kembali ke Beranda" ke="/" />
      </main>
    );
  }

  const jumlahLot = daftarLot.data?.length ?? 0;
  const jumlahSelesai = daftarLot.data?.filter((l) => l.berat_aktual_kg !== null && l.berat_aktual_kg !== undefined).length ?? 0;
  const semuaSelesaiTimbang = jumlahLot > 0 && jumlahSelesai === jumlahLot;
  const sudahBerangkat = slot.data?.status === "JALAN" || slot.data?.status === "SELESAI";

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6 pb-24">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-tanah">Muat</h1>
        <p className="angka text-base text-tanah/70">{slot.data?.kode ?? (slotId ? "Memuat kode slot…" : "")}</p>
      </header>

      {slot.isError && (
        <div className="flex flex-col items-start gap-3 rounded-lg border-2 border-tanah-liat/40 p-4">
          <p className="text-base text-tanah-liat">Gagal memuat data slot.</p>
          <Tombol varian="sekunder" onClick={() => slot.refetch()}>
            Coba lagi
          </Tombol>
        </div>
      )}

      {sudahBerangkat && (
        <section className="flex flex-col items-center gap-4 rounded-lg border-2 border-daun bg-daun/10 p-6 text-center">
          <p className="text-lg font-semibold text-tanah">
            Muat selesai. Kiriman sudah {slot.data?.status === "SELESAI" ? "diterima" : "berangkat"}.
          </p>
          <Link
            to={`/slot/${slotId}/lacak`}
            className="inline-flex min-h-sentuh items-center justify-center gap-2 rounded-md bg-daun px-5 text-base font-semibold text-kertas"
          >
            Lihat pelacakan →
          </Link>
        </section>
      )}

      {!sudahBerangkat && (
        <>
          {daftarLot.isLoading && <p className="text-base text-tanah/60">Memuat daftar lot…</p>}
          {daftarLot.isError && (
            <div className="flex flex-col items-start gap-3 rounded-lg border-2 border-tanah-liat/40 p-4">
              <p className="text-base text-tanah-liat">Gagal memuat daftar lot.</p>
              <Tombol varian="sekunder" onClick={() => daftarLot.refetch()}>
                Coba lagi
              </Tombol>
            </div>
          )}
          {daftarLot.data?.length === 0 && (
            <KeadaanKosong pesan="Belum ada lot untuk dimuat. Tutup slot ini dahulu di layar Detail Slot." />
          )}

          {jumlahLot > 0 && (
            <section
              aria-label="Progres timbang"
              className="flex items-center justify-between rounded-lg border-2 border-kabut px-4 py-3"
            >
              <p className="text-base font-medium text-tanah">
                <span className="angka font-bold">{jumlahSelesai}</span> dari{" "}
                <span className="angka font-bold">{jumlahLot}</span> lot selesai ditimbang
              </p>
            </section>
          )}

          <section aria-label="Daftar lot" className="flex flex-col gap-4">
            {daftarLot.data?.map((lot) => (
              <KartuLotMuat
                key={lot.id}
                lot={lot}
                sedangMenyimpan={muatLot.isPending && muatLot.variables?.lotId === lot.id}
                gagalMenyimpan={muatLot.isError && muatLot.variables?.lotId === lot.id}
                onSimpan={(body) => muatLot.mutate({ lotId: lot.id, body })}
              />
            ))}
          </section>

          {jumlahLot > 0 && (
            <div className="flex flex-col gap-2">
              {selesaiMuat.isError && (
                <p role="alert" className="text-sm text-tanah-liat">
                  Gagal menyelesaikan muat. Pastikan semua lot sudah ditimbang, lalu coba lagi.
                </p>
              )}
              <Tombol
                type="button"
                varian="aksi"
                disabled={!semuaSelesaiTimbang || selesaiMuat.isPending}
                onClick={() => selesaiMuat.mutate()}
              >
                {selesaiMuat.isPending ? "Memberangkatkan…" : "Selesai muat"}
              </Tombol>
            </div>
          )}
        </>
      )}
    </main>
  );
}
