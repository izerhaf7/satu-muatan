/** Layar Lacak (§9.6, semua peran) — timeline status, peta rute, estimasi tiba,
 *  grafik telemetri, dan kendali simulasi posisi khusus Petugas (K5/K13).
 *  Poll 3 detik selama belum TIBA. */

import { useEffect, useState } from "react";
import { PlayCircle, StepForward, Timer } from "lucide-react";
import { useParams } from "react-router-dom";

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { Skeleton } from "@/komponen/Skeleton";
import Tombol from "@/komponen/Tombol";
import {
  useGeserPosisi,
  useMajukanPengiriman,
  usePengirimanSlot,
  useSlotUntukLacak,
  useTelemetriSlot,
} from "@/hooks/useLacak";
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

  // K14: tanpa id, SEMUA query di bawah `enabled: false`. Di react-query v5
  // query yang mati punya isLoading=false dan isError=false, jadi layar dulu
  // merender header saja lalu berhenti — tampak seperti halaman kosong. Ikuti
  // pola DetailSlot: nyatakan keadaan ini secara eksplisit.
  if (!slotId) {
    return (
      <div className="flex flex-col gap-6">
        <HeaderLayar judul="Lacak" kembaliKe="/beranda" />
        <KeadaanKosong pesan="Muatan tidak ditemukan." teksAksi="Kembali ke Beranda" ke="/beranda" />
      </div>
    );
  }

  return <IsiLacak slotId={slotId} pengguna={pengguna} />;
}

function IsiLacak({
  slotId,
  pengguna,
}: {
  slotId: string;
  pengguna: ReturnType<typeof useAuthStore.getState>["pengguna"];
}) {

  const slot = useSlotUntukLacak(slotId);
  const pengiriman = usePengirimanSlot(slotId);
  const majukan = useMajukanPengiriman(slotId);
  const geser = useGeserPosisi(slotId);
  const [jalanOtomatis, setJalanOtomatis] = useState(false);

  const memuat = slot.isLoading || pengiriman.isLoading;

  const belumTutup = pengiriman.isError;

  // K13: koordinat tujuan ikut di payload muatan — tujuan kini bebas ditulis
  // petani, jadi peta tidak boleh lagi bergantung pada katalog penerima.
  const tujuanDenganKoordinat =
    slot.data?.tujuan.map((t) => ({
      lat: t.lat,
      lng: t.lng,
      label: `${t.urutan}. ${t.nama_penerima}`,
    })) ?? [];

  const jejak =
    pengiriman.data?.jejak
      .filter((j) => j.lat !== null && j.lat !== undefined && j.lng !== null && j.lng !== undefined)
      .map((j) => ({ lat: j.lat as number, lng: j.lng as number })) ?? [];
  const jejakTerakhir = jejak.at(-1);
  const posisiTerakhir = jejakTerakhir ? { ...jejakTerakhir, label: "Posisi terakhir" } : null;

  const sudahTiba = Boolean(pengiriman.data?.timeline.tiba);
  const telemetri = useTelemetriSlot(slotId, sudahTiba);
  const pengirimanId = pengiriman.data?.id;
  const sudahBerangkat = Boolean(pengiriman.data?.timeline.berangkat);

  // Mode "jalan otomatis": posisi maju sendiri tiap beberapa detik supaya peta
  // terlihat hidup tanpa perlu diklik terus saat presentasi.
  useEffect(() => {
    if (!jalanOtomatis || sudahTiba || !pengirimanId || !sudahBerangkat) return;
    const timer = window.setInterval(() => {
      if (!geser.isPending) geser.mutate(pengirimanId);
    }, 2000);
    return () => window.clearInterval(timer);
  }, [jalanOtomatis, sudahTiba, pengirimanId, sudahBerangkat, geser]);

  useEffect(() => {
    if (sudahTiba) setJalanOtomatis(false);
  }, [sudahTiba]);

  return (
    <div className="flex flex-col gap-6">
      <HeaderLayar
        judul="Lacak"
        subjudul={slot.data ? `${slot.data.kode} · ${formatAngka(slot.data.jarak_km)} km` : undefined}
        kembaliKe={`/slot/${slotId}`}
      />

      {slot.isError && <KartuGalat pesan="Gagal memuat data slot." onCobaLagi={() => slot.refetch()} />}

      {memuat && (
        <div className="flex flex-col gap-6">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      )}

      {belumTutup && !memuat && (
        <KeadaanKosong pesan="Muatan ini belum punya pengiriman untuk dilacak. Tutup muatan dahulu di layar Detail Muatan." />
      )}

      {/* K14: celah antara percobaan pertama gagal dan percobaan ulang —
          isLoading & isError sama-sama false di sana, dan layar dulu kosong. */}
      {!memuat && !belumTutup && !pengiriman.data && (
        <KeadaanKosong pesan="Menyiapkan data pengiriman…" />
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
                jejak={jejak}
                rutePolyline={pengiriman.data.rute_polyline}
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
            <div className="kartu-datar flex flex-col gap-2.5 p-4">
              <p className="text-keterangan font-bold uppercase tracking-wide text-tanah/50">Kendali demo</p>
              {(majukan.isError || geser.isError) && (
                <p role="alert" className="text-keterangan text-tanah-liat">
                  Gagal memajukan simulasi. Coba lagi.
                </p>
              )}

              {sudahBerangkat ? (
                <>
                  <Tombol
                    type="button"
                    varian="sekunder"
                    ikon={StepForward}
                    sedangProses={geser.isPending && !jalanOtomatis}
                    disabled={jalanOtomatis}
                    onClick={() => pengirimanId && geser.mutate(pengirimanId)}
                  >
                    Majukan posisi
                  </Tombol>
                  <Tombol
                    type="button"
                    varian={jalanOtomatis ? "aksi" : "halus"}
                    ikon={PlayCircle}
                    onClick={() => setJalanOtomatis((v) => !v)}
                  >
                    {jalanOtomatis ? "Hentikan jalan otomatis" : "Jalan otomatis"}
                  </Tombol>
                  <p className="text-keterangan text-tanah/50">
                    Posisi bergerak sepanjang rute — manual atau otomatis tiap 2 detik.
                  </p>
                </>
              ) : (
                <>
                  <Tombol
                    type="button"
                    varian="halus"
                    sedangProses={majukan.isPending}
                    onClick={() => pengirimanId && majukan.mutate(pengirimanId)}
                  >
                    Majukan status
                  </Tombol>
                  <p className="text-keterangan text-tanah/50">
                    Simulasi vendor demo — memajukan status pengiriman satu langkah tanpa menunggu waktu asli.
                  </p>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
