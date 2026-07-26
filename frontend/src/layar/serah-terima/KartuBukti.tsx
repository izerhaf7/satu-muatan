/** Detail bukti + keputusan serah terima satu lot (§9.7). Dua mode:
 *  - `bukti.serah_terima` sudah ada -> tampilan baca-saja + penjelasan atribusi
 *    (guard anti-submit-ganda, sesuai kontrak: serah_terima non-null di server).
 *  - belum ada -> tiga tombol keputusan, form potongan/tolak, kirim. */

import { useState, type ReactNode } from "react";
import {
  AlertTriangle,
  Check,
  Clock,
  Percent,
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
import Penggeser from "@/komponen/Penggeser";
import Tombol from "@/komponen/Tombol";
import type { components } from "@/api/client";
import { formatAngka } from "@/utils/format";

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
};

// Tiga nada palet, satu per hasil (K12): PETANI = fault terbukti di titik muat (tanah-liat),
// LOGISTIK = fault di perjalanan, bukan salah petani (kabut, netral), TIDAK_TERBUKTI = bersih (daun).
const kelasAtribusi: Record<Atribusi, string> = {
  PETANI: "border-tanah-liat/40 bg-tanah-liat/5 text-tanah-liat",
  LOGISTIK: "border-kabut bg-kabut/30 text-tanah",
  TIDAK_TERBUKTI: "border-daun/40 bg-daun/5 text-daun",
};

function formatWaktu(waktu: string): string {
  return new Date(waktu).toLocaleString("id-ID", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function KartuBukti({ bukti, onKirim, sedangMengirim, gagalMengirim }: KartuBuktiProps) {
  const [keputusan, setKeputusan] = useState<KeputusanSerahTerima | null>(null);
  const [persenPotongan, setPersenPotongan] = useState(10);
  const [alasan, setAlasan] = useState("");
  const [fotoBongkar, setFotoBongkar] = useState<string | null>(null);

  const { lot } = bukti;

  const butuhAlasan = keputusan === "POTONG" || keputusan === "TOLAK";
  const bisaKirim = keputusan !== null && (!butuhAlasan || alasan.trim().length > 0);

  function kirim() {
    if (!keputusan || !bisaKirim) return;
    onKirim({
      keputusan,
      persen_potongan: keputusan === "TOLAK" ? 100 : keputusan === "POTONG" ? persenPotongan : 0,
      alasan: alasan.trim() || null,
      foto_bongkar_base64: fotoBongkar,
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
          {st.persen_potongan > 0 && (
            <span className="angka">
              {" "}
              · potongan {formatAngka(st.persen_potongan)}%
            </span>
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

      {!keputusan && (
        <div className="flex flex-col gap-2.5">
          <Tombol type="button" varian="aksi" ikon={Check} className="w-full" onClick={() => setKeputusan("TERIMA")}>
            Terima
          </Tombol>
          <Tombol type="button" varian="sekunder" ikon={Percent} className="w-full" onClick={() => setKeputusan("POTONG")}>
            Terima dengan potongan
          </Tombol>
          <Tombol type="button" varian="bahaya" ikon={X} className="w-full" onClick={() => setKeputusan("TOLAK")}>
            Tolak
          </Tombol>
        </div>
      )}

      {keputusan && (
        <div className="kartu-datar flex flex-col gap-4 p-3">
          <p className="text-base font-semibold text-tanah">{labelKeputusan[keputusan]}</p>

          {keputusan === "POTONG" && (
            <Penggeser
              label="Potongan"
              value={persenPotongan}
              onChange={(e) => setPersenPotongan(Number(e.target.value))}
              min={1}
              max={99}
              satuan="%"
            />
          )}

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
  POTONG: "Terima dengan potongan",
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
      </div>

      {lot.cacat_terlihat && (
        <p className="flex items-center gap-2 rounded-lg border-2 border-tanah-liat/40 bg-tanah-liat/5 px-3 py-2 text-keterangan font-medium text-tanah-liat">
          <AlertTriangle aria-hidden className="h-4 w-4 shrink-0" />
          Ada cacat terlihat sejak muat
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
