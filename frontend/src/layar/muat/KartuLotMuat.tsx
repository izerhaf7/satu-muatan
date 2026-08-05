/** Kartu satu lot pada layar Muat (§9.5 + v2 §6.1) — timbang, foto, grade mutu 1–5,
 *  catatan, QR. Form lokal per lot (bukan auto-save) supaya petugas titik kumpul
 *  bisa isi semua field dulu baru menekan "Simpan timbangan" satu kali per lot. */

import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Save, Sprout } from "lucide-react";

import AmbilFoto from "@/komponen/AmbilFoto";
import AreaTeks from "@/komponen/AreaTeks";
import InputTeks from "@/komponen/InputTeks";
import PilihGrade from "@/komponen/PilihGrade";
import RingkasanResi from "@/komponen/RingkasanResi";
import Tombol from "@/komponen/Tombol";
import type { components } from "@/api/client";
import { formatAngka } from "@/utils/format";
import { buatQrDataUrl } from "@/utils/qr";

type LotOut = components["schemas"]["LotOut"];
type MuatPatchRequest = components["schemas"]["MuatPatchRequest"];

interface KartuLotMuatProps {
  lot: LotOut;
  onSimpan: (body: MuatPatchRequest) => void;
  sedangMenyimpan: boolean;
  gagalMenyimpan: boolean;
}

export default function KartuLotMuat({ lot, onSimpan, sedangMenyimpan, gagalMenyimpan }: KartuLotMuatProps) {
  const sudahDitimbang = lot.berat_aktual_kg !== null && lot.berat_aktual_kg !== undefined;

  const [beratAktual, setBeratAktual] = useState(String(lot.berat_aktual_kg ?? lot.volume_kg));
  const [foto, setFoto] = useState<string | null>(lot.foto_muat ?? null);
  const [gradeAsal, setGradeAsal] = useState(lot.grade_asal);
  const [catatan, setCatatan] = useState(lot.catatan_muat ?? "");
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(null);

  useEffect(() => {
    let batal = false;
    buatQrDataUrl(lot.kode_qr).then((url) => {
      if (!batal) setQrDataUrl(url);
    });
    return () => {
      batal = true;
    };
  }, [lot.kode_qr]);

  const beratValid = Number(beratAktual) > 0;
  // K14: FOTO WAJIB. Petugas adalah penghubung yang menyaksikan barang berpindah
  // tangan; tanpa fotonya, atribusi mutu jadi klaim tanpa sandaran. Server ikut
  // menolak — ini hanya supaya penolakannya tidak datang belakangan.
  const adaFoto = Boolean(foto);
  const bisaSimpan = beratValid && adaFoto;

  function simpan() {
    if (!bisaSimpan) return;
    onSimpan({
      berat_aktual_kg: Number(beratAktual),
      foto_muat_base64: foto,
      grade_asal: gradeAsal,
      catatan_muat: catatan || null,
    });
  }

  return (
    <div
      className={`kartu-tonjol flex flex-col gap-4 p-4 transition-colors duration-cepat ${
        sudahDitimbang ? "border-daun/30 bg-daun/5" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-daun/10 text-daun">
            <Sprout aria-hidden className="h-5 w-5" strokeWidth={2.25} />
          </span>
          <div>
            <p className="text-base font-semibold text-tanah">{lot.nama_petani}</p>
            <p className="text-keterangan text-tanah/70">
              {lot.nama_komoditas} · komitmen <span className="angka">{formatAngka(lot.volume_kg)}</span> kg
            </p>
            {lot.nama_penerima && <p className="text-keterangan text-tanah/60">Tujuan: {lot.nama_penerima}</p>}
          </div>
        </div>
        {sudahDitimbang && (
          <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-daun px-2.5 py-1 text-keterangan font-semibold text-kertas">
            <CheckCircle2 aria-hidden className="h-3.5 w-3.5" />
            Selesai
          </span>
        )}
      </div>

      <InputTeks
        label="Berat aktual (kg)"
        id={`berat-${lot.id}`}
        type="number"
        inputMode="decimal"
        min={0.1}
        step="0.1"
        value={beratAktual}
        onChange={(e) => setBeratAktual(e.target.value)}
        className="angka text-lg font-semibold"
      />

      <div className="flex flex-col gap-1.5">
        <AmbilFoto label="Foto muat (wajib)" nilai={foto} onUbah={setFoto} />
        {!adaFoto && (
          <p className="text-keterangan text-tanah-liat">
            Foto wajib — inilah bukti kondisi barang saat berangkat.
          </p>
        )}
      </div>

      <PilihGrade label="Grade mutu saat muat" nilai={gradeAsal} onUbah={setGradeAsal} />

      <AreaTeks
        label="Catatan (opsional)"
        id={`catatan-${lot.id}`}
        value={catatan}
        onChange={(e) => setCatatan(e.target.value)}
        rows={2}
      />

      {gagalMenyimpan && (
        <p role="alert" className="flex items-center gap-1.5 text-keterangan font-medium text-tanah-liat">
          <AlertCircle aria-hidden className="h-4 w-4 shrink-0" />
          Gagal menyimpan timbangan. Coba lagi.
        </p>
      )}

      <Tombol
        type="button"
        varian="aksi"
        ikon={Save}
        sedangProses={sedangMenyimpan}
        disabled={!bisaSimpan}
        onClick={simpan}
      >
        {sudahDitimbang ? "Perbarui timbangan" : "Simpan timbangan"}
      </Tombol>

      <div className="flex flex-col items-center gap-2 border-t border-kabut pt-4">
        <div className="rounded-xl border-2 border-kabut bg-kertas p-3">
          {qrDataUrl && <img src={qrDataUrl} alt={`QR lot ${lot.kode_qr}`} className="h-28 w-28" />}
        </div>
        <RingkasanResi resi={[{ lot_id: lot.id, kode_qr: lot.kode_qr }]} />
      </div>
    </div>
  );
}
