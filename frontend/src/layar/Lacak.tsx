/** Layar Lacak (§9.6, semua peran) — timeline status, peta rute, estimasi tiba,
 *  dan tombol simulasi "Majukan (demo)" khusus Koperasi (K5). Poll 3 detik selama belum TIBA. */

import { useParams } from "react-router-dom";

import KeadaanKosong from "@/komponen/KeadaanKosong";
import Tombol from "@/komponen/Tombol";
import { useDaftarPenerima } from "@/hooks/usePenerima";
import { useMajukanPengiriman, usePengirimanSlot, useSlotUntukLacak } from "@/hooks/useLacak";
import { useAuthStore } from "@/stores/authStore";
import { formatAngka } from "@/utils/format";

import PetaLacak from "./lacak/PetaLacak";
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

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6 pb-24">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-tanah">Lacak</h1>
        <p className="angka text-base text-tanah/70">
          {slot.data ? `${slot.data.kode} · ${formatAngka(slot.data.jarak_km)} km` : "Memuat…"}
        </p>
      </header>

      {memuat && <p className="text-base text-tanah/60">Memuat data pengiriman…</p>}

      {belumTutup && !memuat && (
        <KeadaanKosong pesan="Slot ini belum punya pengiriman untuk dilacak. Tutup slot dahulu di layar Detail Slot." />
      )}

      {!belumTutup && pengiriman.data && (
        <>
          <section aria-label="Status pengiriman" className="rounded-lg border-2 border-kabut p-4">
            <TimelineLacak timeline={pengiriman.data.timeline} />
          </section>

          {tujuanDenganKoordinat.length > 0 && slot.data && (
            <section aria-label="Peta rute">
              <PetaLacak
                gudang={{ lat: slot.data.koperasi.lat, lng: slot.data.koperasi.lng, label: slot.data.koperasi.nama }}
                tujuan={tujuanDenganKoordinat}
                posisiTerakhir={posisiTerakhir}
              />
            </section>
          )}

          <section aria-label="Estimasi tiba" className="flex flex-col gap-1 rounded-lg border-2 border-kabut p-4">
            {sudahTiba ? (
              <p className="text-base font-semibold text-tanah">
                Sudah tiba{pengiriman.data.timeline.tiba ? ` · ${formatWaktu(pengiriman.data.timeline.tiba)}` : ""}
              </p>
            ) : (
              <p className="text-base font-semibold text-tanah">
                Estimasi tiba: {pengiriman.data.estimasi_tiba ? formatWaktu(pengiriman.data.estimasi_tiba) : "—"}
              </p>
            )}
            <p className="text-sm text-tanah/60">
              Ambang rute ini: <span className="angka">{formatAngka(pengiriman.data.ambang_transit_menit)}</span> menit
            </p>
          </section>

          {pengguna?.peran === "KOPERASI" && !sudahTiba && (
            <div className="flex flex-col gap-2">
              {majukan.isError && (
                <p role="alert" className="text-sm text-tanah-liat">
                  Gagal memajukan simulasi. Coba lagi.
                </p>
              )}
              <Tombol
                type="button"
                varian="sekunder"
                disabled={majukan.isPending}
                onClick={() => pengiriman.data && majukan.mutate(pengiriman.data.id)}
              >
                {majukan.isPending ? "Memproses…" : "Majukan (demo)"}
              </Tombol>
              <p className="text-sm text-tanah/50">
                Simulasi vendor demo — memajukan status pengiriman satu langkah tanpa menunggu waktu asli.
              </p>
            </div>
          )}
        </>
      )}
    </main>
  );
}
