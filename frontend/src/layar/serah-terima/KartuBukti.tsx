/** Detail bukti + keputusan serah terima satu lot (§9.7). Dua mode:
 *  - `bukti.serah_terima` sudah ada -> tampilan baca-saja + penjelasan atribusi
 *    (guard anti-submit-ganda, sesuai kontrak: serah_terima non-null di server).
 *  - belum ada -> indeks mutu dulu, baru dua tombol keputusan.
 *
 *  K14, tiga perubahan aturan produk:
 *  1. **Mutu sebelum keputusan.** Indeks mutu sistem ditampilkan di atas tombol,
 *     bukan disembunyikan sampai keputusan terkirim.
 *  2. **Tanpa potongan.** "Terima dengan potongan" dihapus seluruhnya — penerima
 *     tidak boleh punya tuas komersial atas mutu yang dia nilai sendiri.
 *  3. **Tolak bersyarat.** Tombol Tolak hanya muncul kalau penurunan mutu yang
 *     DIUKUR SISTEM melewati ambang; server menegakkan syarat yang sama. */

import { useState, type ReactNode } from "react";
import {
  AlertTriangle,
  Check,
  Clock,
  Lock,
  RotateCcw,
  Scale,
  Send,
  Sprout,
  Timer,
  X,
  type LucideIcon,
} from "lucide-react";

import AmbilFoto from "@/komponen/AmbilFoto";
import AreaTeks from "@/komponen/AreaTeks";
import Tombol from "@/komponen/Tombol";
import PilihGrade, { LABEL_GRADE } from "@/komponen/PilihGrade";
import type { components } from "@/api/client";
import { formatAngka } from "@/utils/format";

import KartuIndeksMutu from "./KartuIndeksMutu";

type BuktiLotOut = components["schemas"]["BuktiLotOut"];
type SerahTerimaCreate = components["schemas"]["SerahTerimaCreate"];
type KeputusanSerahTerima = components["schemas"]["KeputusanSerahTerima"];
type Atribusi = components["schemas"]["Atribusi"];

interface KartuBuktiProps {
  bukti: BuktiLotOut;
  onKirim: (body: SerahTerimaCreate) => void;
  sedangMengirim: boolean;
  gagalMengirim: boolean;
}

const labelAtribusi: Record<Atribusi, string> = {
  PETANI: "Petani",
  LOGISTIK: "Logistik",
  TIDAK_TERBUKTI: "Tidak terbukti",
  NORMAL: "Normal",
};

// Tiga nada palet, satu per hasil (K12): PETANI = fault terbukti di titik muat (tanah-liat),
// LOGISTIK = fault di perjalanan, bukan salah petani (kabut, netral), TIDAK_TERBUKTI = bersih (daun).
// NORMAL (§6/C3): tidak ada penurunan mutu — netral (kabut).
const kelasAtribusi: Record<Atribusi, string> = {
  PETANI: "border-tanah-liat/40 bg-tanah-liat/5 text-tanah-liat",
  LOGISTIK: "border-kabut bg-kabut/30 text-tanah",
  TIDAK_TERBUKTI: "border-daun/40 bg-daun/5 text-daun",
  NORMAL: "border-kabut bg-kabut/30 text-tanah",
};

function formatWaktu(waktu: string): string {
  return new Date(waktu).toLocaleString("id-ID", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function KartuBukti({ bukti, onKirim, sedangMengirim, gagalMengirim }: KartuBuktiProps) {
  const [keputusan, setKeputusan] = useState<KeputusanSerahTerima | null>(null);
  const [alasan, setAlasan] = useState("");
  const [fotoBongkar, setFotoBongkar] = useState<string | null>(null);
  // K14: TIDAK lagi default ke grade_asal. Dulu penerima yang menolak tanpa
  // menyentuh penggeser menghasilkan grade_tiba == grade_asal, sehingga atribusi
  // menjawab "Tidak ada penurunan mutu" pada lot yang baru saja dia tolak.
  const [gradeTiba, setGradeTiba] = useState<number | null>(null);

  const { lot } = bukti;
  const bolehTolak = bukti.mutu?.boleh_tolak ?? false;

  const butuhAlasan = keputusan === "TOLAK";
  const bisaKirim =
    keputusan !== null && gradeTiba !== null && (!butuhAlasan || alasan.trim().length > 0);

  function kirim() {
    if (!keputusan || gradeTiba === null || !bisaKirim) return;
    onKirim({
      keputusan,
      alasan: alasan.trim() || null,
      foto_bongkar_base64: fotoBongkar,
      grade_tiba: gradeTiba,
    });
  }

  // --- Mode baca-saja: sudah diserahterimakan --------------------------------
  if (bukti.serah_terima) {
    const st = bukti.serah_terima;
    return (
      <div className="kartu-tonjol flex flex-col gap-4 p-4">
        <BuktiRingkas lot={lot} bukti={bukti} />

        <div className="rounded-lg bg-tanah/5 px-3 py-2 text-base text-tanah">
          Keputusan: <span className="font-semibold">{labelKeputusan[st.keputusan]}</span>
          {st.indeks_mutu !== null && st.indeks_mutu !== undefined && (
            <span className="angka"> · indeks mutu {formatAngka(st.indeks_mutu)}</span>
          )}
        </div>

        <PanelAtribusi atribusi={st.atribusi} penjelasan={st.penjelasan} />
      </div>
    );
  }

  // --- Mode keputusan ----------------------------------------------------------
  return (
    <div className="kartu-tonjol flex flex-col gap-4 p-4">
      <BuktiRingkas lot={lot} bukti={bukti} />

      {/* K14: mutu DULU, keputusan belakangan. */}
      {bukti.mutu && <KartuIndeksMutu mutu={bukti.mutu} />}

      <PilihGrade
        label="Grade mutu saat tiba"
        nilai={gradeTiba ?? 0}
        onUbah={setGradeTiba}
      />
      {gradeTiba === null && (
        <p className="text-keterangan text-tanah/55">
          Pilih dulu grade saat tiba — penilaianmu ikut menentukan atribusi.
        </p>
      )}

      {!keputusan && (
        <div className="flex flex-col gap-2.5">
          <Tombol type="button" varian="aksi" ikon={Check} className="w-full" onClick={() => setKeputusan("TERIMA")}>
            Terima
          </Tombol>
          {bolehTolak ? (
            <Tombol type="button" varian="bahaya" ikon={X} className="w-full" onClick={() => setKeputusan("TOLAK")}>
              Tolak
            </Tombol>
          ) : (
            <p className="flex items-start gap-2 rounded-lg border-2 border-kabut bg-kabut/25 px-3 py-2.5 text-keterangan text-tanah/70">
              <Lock aria-hidden className="mt-0.5 h-4 w-4 shrink-0 text-tanah/45" />
              Penolakan tidak tersedia untuk kiriman ini. Penurunan mutu yang terukur belum melewati ambang, jadi
              barang harus diterima — keberatanmu tetap tercatat lewat grade tiba dan atribusi.
            </p>
          )}
        </div>
      )}

      {keputusan && (
        <div className="kartu-datar flex flex-col gap-4 p-3">
          <p className="text-base font-semibold text-tanah">{labelKeputusan[keputusan]}</p>

          {butuhAlasan && (
            <AreaTeks
              label="Alasan (wajib diisi)"
              id="alasan"
              value={alasan}
              onChange={(e) => setAlasan(e.target.value)}
              rows={2}
              required
              placeholder="Jelaskan kondisi barang saat diterima"
            />
          )}

          <AmbilFoto label="Foto bongkar (opsional)" nilai={fotoBongkar} onUbah={setFotoBongkar} />

          {gagalMengirim && (
            <p role="alert" className="text-keterangan text-tanah-liat">
              Gagal mengirim keputusan. Coba lagi.
            </p>
          )}

          <div className="flex flex-col gap-2">
            <Tombol type="button" varian="aksi" ikon={Send} sedangProses={sedangMengirim} disabled={!bisaKirim} onClick={kirim}>
              Kirim keputusan
            </Tombol>
            <Tombol
              type="button"
              varian="sekunder"
              ikon={RotateCcw}
              disabled={sedangMengirim}
              onClick={() => setKeputusan(null)}
            >
              Batal, pilih ulang
            </Tombol>
          </div>
        </div>
      )}
    </div>
  );
}

const labelKeputusan: Record<KeputusanSerahTerima, string> = {
  TERIMA: "Terima",
  TOLAK: "Tolak",
};

function BuktiRingkas({ lot, bukti }: { lot: BuktiLotOut["lot"]; bukti: BuktiLotOut }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-3">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-daun/10 text-daun">
          <Sprout aria-hidden className="h-5 w-5" strokeWidth={2.25} />
        </span>
        <div>
          <p className="text-base font-semibold text-tanah">{lot.nama_petani}</p>
          <p className="text-keterangan text-tanah/70">{lot.nama_komoditas}</p>
        </div>
      </div>

      {lot.foto_muat && (
        <img src={lot.foto_muat} alt="Foto saat muat" className="h-48 w-full rounded-lg border-2 border-kabut object-cover" />
      )}

      <div className="flex flex-col gap-2.5 rounded-lg border-2 border-kabut p-3">
        <BarisFakta ikon={Scale} label="Berat">
          {lot.berat_aktual_kg !== null && lot.berat_aktual_kg !== undefined ? `${formatAngka(lot.berat_aktual_kg)} kg` : "—"}
        </BarisFakta>
        <BarisFakta ikon={Clock} label="Waktu muat">
          {lot.waktu_muat ? formatWaktu(lot.waktu_muat) : "—"}
        </BarisFakta>
        <BarisFakta ikon={Timer} label="Waktu tempuh vs ambang">
          {bukti.durasi_transit_berjalan_menit !== null && bukti.durasi_transit_berjalan_menit !== undefined
            ? `${formatAngka(bukti.durasi_transit_berjalan_menit)} / ${formatAngka(bukti.ambang_transit_menit)} mnt`
            : `— / ${formatAngka(bukti.ambang_transit_menit)} mnt`}
        </BarisFakta>
        <BarisFakta ikon={Sprout} label="Grade saat muat">
          {LABEL_GRADE[lot.grade_asal] ?? lot.grade_asal}
        </BarisFakta>
      </div>

      {lot.grade_asal < 3 && (
        <p className="flex items-center gap-2 rounded-lg border-2 border-tanah-liat/40 bg-tanah-liat/5 px-3 py-2 text-keterangan font-medium text-tanah-liat">
          <AlertTriangle aria-hidden className="h-4 w-4 shrink-0" />
          Grade saat muat sudah di bawah standar ({LABEL_GRADE[lot.grade_asal]})
        </p>
      )}
    </div>
  );
}

function BarisFakta({ ikon: Ikon, label, children }: { ikon: LucideIcon; label: string; children: ReactNode }) {
  return (
    <div className="flex items-center gap-2.5">
      <Ikon aria-hidden className="h-4 w-4 shrink-0 text-tanah/50" strokeWidth={2.25} />
      <p className="flex-1 text-keterangan text-tanah/60">{label}</p>
      <p className="angka text-base font-semibold text-tanah">{children}</p>
    </div>
  );
}

function PanelAtribusi({ atribusi, penjelasan }: { atribusi: Atribusi; penjelasan: string }) {
  return (
    <div className={`flex flex-col gap-2 rounded-xl border-2 p-4 ${kelasAtribusi[atribusi]}`}>
      <p className="text-keterangan font-bold uppercase tracking-wide opacity-80">Atribusi · {labelAtribusi[atribusi]}</p>
      <p className="text-xl font-bold leading-snug">{penjelasan}</p>
    </div>
  );
}
