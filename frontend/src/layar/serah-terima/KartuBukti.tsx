/** Detail bukti + keputusan serah terima satu lot (§9.7). Dua mode:
 *  - `bukti.serah_terima` sudah ada -> tampilan baca-saja + penjelasan atribusi
 *    (guard anti-submit-ganda, sesuai kontrak: serah_terima non-null di server).
 *  - belum ada -> tiga tombol keputusan, form potongan/tolak, kirim. */

import { useState } from "react";

import AmbilFoto from "@/komponen/AmbilFoto";
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

const kelasAtribusi: Record<Atribusi, string> = {
  PETANI: "border-tanah-liat text-tanah-liat",
  LOGISTIK: "border-tanah-liat text-tanah-liat",
  TIDAK_TERBUKTI: "border-daun text-daun",
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
      <div className="flex flex-col gap-4 rounded-lg border-2 border-kabut p-4">
        <BuktiRingkas lot={lot} bukti={bukti} />

        <div className="rounded-md bg-kabut/40 px-3 py-2 text-sm text-tanah">
          Keputusan: <span className="font-semibold">{labelKeputusan[st.keputusan]}</span>
          {st.persen_potongan > 0 && ` · potongan ${formatAngka(st.persen_potongan)}%`}
        </div>

        <PanelAtribusi atribusi={st.atribusi} penjelasan={st.penjelasan} />
      </div>
    );
  }

  // --- Mode keputusan ----------------------------------------------------------
  return (
    <div className="flex flex-col gap-4 rounded-lg border-2 border-kabut p-4">
      <BuktiRingkas lot={lot} bukti={bukti} />

      {!keputusan && (
        <div className="flex flex-col gap-3">
          <Tombol type="button" varian="aksi" onClick={() => setKeputusan("TERIMA")}>
            Terima
          </Tombol>
          <Tombol type="button" varian="sekunder" onClick={() => setKeputusan("POTONG")}>
            Terima dengan potongan
          </Tombol>
          <Tombol type="button" varian="bahaya" onClick={() => setKeputusan("TOLAK")}>
            Tolak
          </Tombol>
        </div>
      )}

      {keputusan && (
        <div className="flex flex-col gap-4 rounded-md border-2 border-kabut p-3">
          <p className="text-base font-semibold text-tanah">{labelKeputusan[keputusan]}</p>

          {keputusan === "POTONG" && (
            <div className="flex flex-col gap-1.5">
              <label htmlFor="persen-potongan" className="text-base font-medium text-tanah">
                Potongan: <span className="angka font-bold">{persenPotongan}%</span>
              </label>
              <input
                id="persen-potongan"
                type="range"
                min={1}
                max={99}
                value={persenPotongan}
                onChange={(e) => setPersenPotongan(Number(e.target.value))}
                className="h-8"
              />
            </div>
          )}

          {butuhAlasan && (
            <div className="flex flex-col gap-1.5">
              <label htmlFor="alasan" className="text-base font-medium text-tanah">
                Alasan <span className="text-tanah-liat">*</span>
              </label>
              <textarea
                id="alasan"
                value={alasan}
                onChange={(e) => setAlasan(e.target.value)}
                rows={2}
                required
                className="rounded-md border-2 border-kabut bg-kertas px-4 py-2 text-base text-tanah focus:border-daun"
                placeholder="Jelaskan kondisi barang saat diterima"
              />
            </div>
          )}

          <AmbilFoto label="Foto bongkar (opsional)" nilai={fotoBongkar} onUbah={setFotoBongkar} />

          {gagalMengirim && (
            <p role="alert" className="text-sm text-tanah-liat">
              Gagal mengirim keputusan. Coba lagi.
            </p>
          )}

          <div className="flex flex-col gap-2">
            <Tombol type="button" varian="aksi" disabled={!bisaKirim || sedangMengirim} onClick={kirim}>
              {sedangMengirim ? "Mengirim…" : "Kirim keputusan"}
            </Tombol>
            <Tombol type="button" varian="sekunder" disabled={sedangMengirim} onClick={() => setKeputusan(null)}>
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
      <div>
        <p className="text-base font-semibold text-tanah">{lot.nama_petani}</p>
        <p className="text-sm text-tanah/70">{lot.nama_komoditas}</p>
      </div>

      {lot.foto_muat && (
        <img src={lot.foto_muat} alt="Foto saat muat" className="max-h-48 w-auto rounded-md border-2 border-kabut object-cover" />
      )}

      <dl className="grid grid-cols-2 gap-x-3 gap-y-2 text-base">
        <dt className="text-tanah/60">Berat</dt>
        <dd className="angka text-tanah">{lot.berat_aktual_kg !== null && lot.berat_aktual_kg !== undefined ? `${formatAngka(lot.berat_aktual_kg)} kg` : "—"}</dd>

        <dt className="text-tanah/60">Waktu muat</dt>
        <dd className="angka text-tanah">{lot.waktu_muat ? formatWaktu(lot.waktu_muat) : "—"}</dd>

        <dt className="text-tanah/60">Waktu tempuh berjalan</dt>
        <dd className="angka text-tanah">
          {bukti.durasi_transit_berjalan_menit !== null && bukti.durasi_transit_berjalan_menit !== undefined
            ? `${formatAngka(bukti.durasi_transit_berjalan_menit)} menit`
            : "—"}
        </dd>

        <dt className="text-tanah/60">Ambang rute</dt>
        <dd className="angka text-tanah">{formatAngka(bukti.ambang_transit_menit)} menit</dd>
      </dl>

      {lot.cacat_terlihat && (
        <p className="rounded-md border-2 border-tanah-liat px-3 py-2 text-sm font-medium text-tanah-liat">
          Ada cacat terlihat sejak muat
        </p>
      )}
    </div>
  );
}

function PanelAtribusi({ atribusi, penjelasan }: { atribusi: Atribusi; penjelasan: string }) {
  return (
    <div className={`flex flex-col gap-2 rounded-lg border-2 p-4 ${kelasAtribusi[atribusi]}`}>
      <p className="text-sm font-semibold uppercase tracking-wide">Atribusi</p>
      <p className="text-xl font-bold">{labelAtribusi[atribusi]}</p>
      <p className="text-base text-tanah">{penjelasan}</p>
    </div>
  );
}
