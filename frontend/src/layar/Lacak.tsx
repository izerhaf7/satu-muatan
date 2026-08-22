/** Layar Lacak (§9.6, semua peran) — timeline, peta, GPS, dan telemetri. */

import { useEffect, useState } from "react";
import { Navigation, Radio, Timer } from "lucide-react";
import { useParams } from "react-router-dom";

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { Skeleton } from "@/komponen/Skeleton";
import Tombol from "@/komponen/Tombol";
import {
  useCatatPosisi,
  usePengirimanSlot,
  useSlotUntukLacak,
  useTetapkanSensorNode,
  useTelemetriSlot,
  useUbahStatusPengiriman,
} from "@/hooks/useLacak";
import { useAuthStore } from "@/stores/authStore";
import { formatAngka } from "@/utils/format";
import type { components } from "@/api/client";

type RuteSegmenOut = components["schemas"]["RuteSegmenOut"];
type PosisiOut = components["schemas"]["PosisiOut"];

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
  const ubahStatus = useUbahStatusPengiriman(slotId);
  const catatPosisi = useCatatPosisi(slotId);
const tetapkanSensor = useTetapkanSensorNode();
  const [gpsAktif, setGpsAktif] = useState(false);

  const memuat = slot.isLoading || pengiriman.isLoading;

  const belumTutup = pengiriman.isError;

  // K13: koordinat tujuan ikut di payload muatan — tujuan kini bebas ditulis
  // petani, jadi peta tidak boleh lagi bergantung pada katalog penerima.
  const tujuanDenganKoordinat =
    slot.data?.tujuan.map((t: RuteSegmenOut) => ({
      lat: t.lat,
      lng: t.lng,
      label: `${t.urutan}. ${t.nama_penerima}`,
    })) ?? [];

  // K14: perhentian penjemputan ikut ditampilkan di peta — kurir berangkat dari
  // lokasinya menuju titik jemput petani, baru ke tujuan akhir.
  const jemputDenganKoordinat =
    slot.data?.jemput.map((j) => ({
      lat: j.lat,
      lng: j.lng,
      label: `Jemput ${j.nama_petani}`,
    })) ?? [];

  const jejak =
    pengiriman.data?.jejak
      .filter((j: PosisiOut) => j.lat !== null && j.lat !== undefined && j.lng !== null && j.lng !== undefined)
      .map((j: PosisiOut) => ({ lat: j.lat as number, lng: j.lng as number })) ?? [];
  const jejakTerakhir = jejak.at(-1);
  const posisiTerakhir = jejakTerakhir ? { ...jejakTerakhir, label: "Posisi terakhir" } : null;

  const sudahTiba = Boolean(pengiriman.data?.timeline.tiba);
  const telemetri = useTelemetriSlot(slotId, sudahTiba);
  const pengirimanId = pengiriman.data?.id;
  const statusPengiriman = pengiriman.data?.status_pengiriman;
  const statusBerikutnya = statusPengiriman === undefined || statusPengiriman === null
    ? "MUAT"
    : statusPengiriman === "MUAT"
      ? "ANTAR"
      : statusPengiriman === "ANTAR"
        ? "BONGKAR_MUAT"
        : null;

  const sampelTerakhir = telemetri.data?.sampel.at(-1);
  const statusSensor = !sampelTerakhir
    ? "OFF"
    : sampelTerakhir.sumber === "SIMULASI"
      ? "SIMULASI"
      : sampelTerakhir.sumber === "SENSOR" && Date.now() - new Date(sampelTerakhir.waktu).getTime() <= 5 * 60 * 1000
        ? "ON"
        : "OFF";

  useEffect(() => {
    if (pengguna?.peran !== "PETUGAS" || !pengirimanId || !["MUAT", "ANTAR", "BONGKAR_MUAT"].includes(statusPengiriman ?? "")) {
      setGpsAktif(false);
      return;
    }
    if (!navigator.geolocation) return;
    const terakhirTerkirim = { value: 0 };
    const watchId = navigator.geolocation.watchPosition(
      (posisi) => {
        setGpsAktif(true);
        const sekarang = Date.now();
        if (!catatPosisi.isPending && (terakhirTerkirim.value === 0 || sekarang - terakhirTerkirim.value >= 30_000)) {
          terakhirTerkirim.value = sekarang;
          catatPosisi.mutate({
            pengirimanId,
            lat: posisi.coords.latitude,
            lng: posisi.coords.longitude,
            akurasi_m: posisi.coords.accuracy,
            waktu: new Date(posisi.timestamp).toISOString(),
          });
        }
      },
      () => setGpsAktif(false),
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 },
    );
    return () => {
      navigator.geolocation.clearWatch(watchId);
      setGpsAktif(false);
    };
  }, [pengguna?.peran, pengirimanId, statusPengiriman, catatPosisi]);

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
                jemput={jemputDenganKoordinat}
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
              {pengiriman.data.eta_provider_menit != null
                ? `Estimasi rute: ${formatAngka(pengiriman.data.eta_provider_menit)} menit (Google)`
                : `Estimasi rute: ${formatAngka(pengiriman.data.ambang_transit_menit)} menit (ambang)`}
            </p>
          </section>

          {telemetri.data?.ringkasan && (
            <section aria-label="Telemetri suhu" className="kartu-tonjol flex flex-col gap-4 p-4 lg:col-span-2">
              <StatusSensor status={statusSensor} sampelTerakhir={sampelTerakhir?.waktu} />
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

          {!telemetri.data?.ringkasan && !telemetri.isLoading && (
            <section aria-label="Status sensor" className="kartu-datar p-4 lg:col-span-2">
              <StatusSensor status={statusSensor} sampelTerakhir={sampelTerakhir?.waktu} />
            </section>
          )}

          {pengguna?.peran === "PETUGAS" && !sudahTiba && (
            <div className="kartu-datar flex flex-col gap-2.5 p-4">
              <div>
                <p className="text-keterangan font-bold uppercase tracking-wide text-tanah/50">Kendali petugas</p>
                <p className="mt-1 text-base font-semibold text-tanah">GPS perjalanan &amp; sensor IoT</p>
                <p className="mt-1 text-keterangan text-tanah/60">
                   Tandai tahap perjalanan sesuai kondisi kendaraan. GPS HP akan dikirim otomatis setelah MUAT.
                </p>
              </div>
              {statusBerikutnya && (
                <Tombol
                  type="button"
                  varian="aksi"
                  ikon={statusBerikutnya === "ANTAR" ? Navigation : Radio}
                  sedangProses={ubahStatus.isPending}
                  onClick={() => pengirimanId && ubahStatus.mutate({ pengirimanId, status: statusBerikutnya })}
                >
                  Tandai {statusBerikutnya.replace("_", " ")}
                </Tombol>
              )}
{gpsAktif && (
                <p className="text-keterangan text-daun">GPS aktif. Biarkan halaman ini terbuka selama perjalanan.</p>
              )}
              <Tombol
                type="button"
                varian="sekunder"
                ikon={Radio}
                sedangProses={tetapkanSensor.isPending}
                onClick={() => tetapkanSensor.mutate({ slotId, node_path: "/sensor" })}
              >
                Cek sensor
              </Tombol>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StatusSensor({ status, sampelTerakhir }: { status: string; sampelTerakhir?: string }) {
  const gaya = status === "ON" ? "text-daun" : status === "SIMULASI" ? "text-tanah-liat" : "text-tanah/55";
  const label = status === "ON" ? "SENSOR: ON" : status === "SIMULASI" ? "SIMULASI" : "SENSOR: OFF";
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-2">
        <Radio aria-hidden className={`h-5 w-5 ${gaya}`} strokeWidth={2.25} />
        <p className={`text-base font-semibold ${gaya}`}>{label}</p>
      </div>
      <p className="text-keterangan text-tanah/55">
        {sampelTerakhir ? `Data terakhir ${formatWaktu(sampelTerakhir)}` : "Belum ada data sensor"}
      </p>
    </div>
  );
}
