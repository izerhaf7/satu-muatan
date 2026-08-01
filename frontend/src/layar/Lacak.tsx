/** Layar Lacak (§9.6, semua peran) — timeline status, peta rute, estimasi tiba,
 *  dan tombol simulasi "Majukan (demo)" khusus Petugas (K5). Poll 3 detik selama belum TIBA. */

import { Timer } from "lucide-react";
import { useParams } from "react-router-dom";

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { Skeleton } from "@/komponen/Skeleton";
import Tombol from "@/komponen/Tombol";
import { useDaftarPenerima } from "@/hooks/usePenerima";
import { useMajukanPengiriman, usePengirimanSlot, useSlotUntukLacak, useTelemetriSlot } from "@/hooks/useLacak";
import { useAuthStore } from "@/stores/authStore";
import { formatAngka } from "@/utils/format";

import PetaLacak from "./lacak/PetaLacak";
import GrafikSuhu from "./lacak/GrafikSuhu";
import TimelineLacak from "./lacak/TimelineLacak";

function formatWaktu(waktu: string): string {
  return new Date(waktu).toLocaleString("id-ID", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Lacak() {
  const { id: slotId } = useParams();
  const pengguna = useAuthStore((s) => s.pengguna);

  const slot = useSlotUntukLacak(slotId);
  const pengiriman = usePengirimanSlot(slotId);
  const daftarPenerima = useDaftarPenerima();
  const majukan = useMajukanPengiriman(slotId);

  const memuat = slot.isLoading || pengiriman.isLoading;

  const belumTutup = pengiriman.isError;

  const tujuanDenganKoordinat =
    slot.data && daftarPenerima.data
      ? slot.data.tujuan
          .map((t) => {
            const penerima = daftarPenerima.data.find((p) => p.id === t.penerima_id);
            return penerima ? { lat: penerima.lat, lng: penerima.lng, label: `${t.urutan}. ${t.nama_penerima}` } : null;
          })
          .filter((t): t is { lat: number; lng: number; label: string } => t !== null)
      : [];

  const jejakTerakhir = pengiriman.data?.jejak.at(-1);
  const posisiTerakhir =
    jejakTerakhir && jejakTerakhir.lat !== null && jejakTerakhir.lng !== null && jejakTerakhir.lat !== undefined && jejakTerakhir.lng !== undefined
      ? { lat: jejakTerakhir.lat, lng: jejakTerakhir.lng, label: "Posisi terakhir" }
      : null;

  const sudahTiba = Boolean(pengiriman.data?.timeline.tiba);
  const telemetri = useTelemetriSlot(slotId, sudahTiba);

  return (
    <div className="flex flex-col gap-6">
      <HeaderLayar
        judul="Lacak"
        subjudul={slot.data ? `${slot.data.kode} · ${formatAngka(slot.data.jarak_km)} km` : undefined}
        kembaliKe={slotId ? `/slot/${slotId}` : "/beranda"}
      />

      {slot.isError && <KartuGalat pesan="Gagal memuat data slot." onCobaLagi={() => slot.refetch()} />}

      {memuat && (
        <div className="flex flex-col gap-6">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      )}

      {belumTutup && !memuat && (
        <KeadaanKosong pesan="Slot ini belum punya pengiriman untuk dilacak. Tutup slot dahulu di layar Detail Slot." />
      )}

      {!belumTutup && pengiriman.data && (
        <div className="flex flex-col gap-6 lg:grid lg:grid-cols-2 lg:items-start">
          <section aria-label="Status pengiriman" className="kartu-tonjol p-4">
            <TimelineLacak timeline={pengiriman.data.timeline} />
          </section>

          {tujuanDenganKoordinat.length > 0 && slot.data && (
            <section aria-label="Peta rute" className="lg:row-span-3">
              <PetaLacak
                gudang={{ lat: slot.data.titik_kumpul.lat, lng: slot.data.titik_kumpul.lng, label: slot.data.titik_kumpul.nama }}
                tujuan={tujuanDenganKoordinat}
                posisiTerakhir={posisiTerakhir}
              />
            </section>
          )}

          <section aria-label="Estimasi tiba" className="kartu-datar flex flex-col gap-1 p-4">
            <div className="flex items-center gap-2">
              <Timer aria-hidden className="h-5 w-5 shrink-0 text-daun" strokeWidth={2.25} />
              {sudahTiba ? (
                <p className="text-base font-semibold text-tanah">
                  Sudah tiba{pengiriman.data.timeline.tiba ? ` · ${formatWaktu(pengiriman.data.timeline.tiba)}` : ""}
                </p>
              ) : (
                <p className="text-base font-semibold text-tanah">
                  Estimasi tiba: {pengiriman.data.estimasi_tiba ? formatWaktu(pengiriman.data.estimasi_tiba) : "—"}
                </p>
              )}
            </div>
            <p className="text-keterangan text-tanah/60">
              Ambang rute ini: <span className="angka">{formatAngka(pengiriman.data.ambang_transit_menit)}</span> menit
            </p>
          </section>

          {telemetri.data?.ringkasan && (
            <section aria-label="Telemetri suhu" className="kartu-tonjol flex flex-col gap-4 p-4 lg:col-span-2">
              <div className="grid grid-cols-3 gap-3">
                <div className="flex flex-col gap-0.5">
                  <p className="angka text-2xl font-bold text-tanah-liat">
                    {telemetri.data.ringkasan.suhu_maks_c.toFixed(1)}°
                  </p>
                  <p className="text-keterangan text-tanah/60">Suhu maks</p>
                </div>
                <div className="flex flex-col gap-0.5">
                  <p className="angka text-2xl font-bold text-tanah">
                    {telemetri.data.ringkasan.suhu_rata_c.toFixed(1)}°
                  </p>
                  <p className="text-keterangan text-tanah/60">Suhu rata-rata</p>
                </div>
                <div className="flex flex-col gap-0.5">
                  <p className="angka text-2xl font-bold text-daun">
                    {telemetri.data.ringkasan.sisa_umur_simpan_persen}%
                  </p>
                  <p className="text-keterangan text-tanah/60">
                    Sisa umur simpan{telemetri.data.ringkasan.nama_komoditas ? ` · ${telemetri.data.ringkasan.nama_komoditas}` : ""}
                  </p>
                </div>
              </div>
              <GrafikSuhu telemetri={telemetri.data} />
            </section>
          )}

          {pengguna?.peran === "PETUGAS" && !sudahTiba && (
            <div className="flex flex-col gap-1.5">
              {majukan.isError && (
                <p role="alert" className="text-keterangan text-tanah-liat">
                  Gagal memajukan simulasi. Coba lagi.
                </p>
              )}
              <Tombol
                type="button"
                varian="halus"
                sedangProses={majukan.isPending}
                onClick={() => pengiriman.data && majukan.mutate(pengiriman.data.id)}
              >
                Majukan (demo)
              </Tombol>
              <p className="text-keterangan text-tanah/50">
                Simulasi vendor demo — memajukan status pengiriman satu langkah tanpa menunggu waktu asli.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
