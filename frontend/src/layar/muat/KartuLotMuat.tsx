/** Kartu satu lot pada layar Muat (§9.5) — timbang, foto, cacat terlihat, catatan, QR.
 *  Form lokal per lot (bukan auto-save) supaya petugas gudang bisa isi semua field dulu
 *  baru menekan "Simpan timbangan" satu kali per lot. */

import { useEffect, useState } from "react";

import AmbilFoto from "@/komponen/AmbilFoto";
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
  const [cacatTerlihat, setCacatTerlihat] = useState(lot.cacat_terlihat);
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

  function simpan() {
    if (!beratValid) return;
    onSimpan({
      berat_aktual_kg: Number(beratAktual),
      foto_muat_base64: foto,
      cacat_terlihat: cacatTerlihat,
      catatan_muat: catatan || null,
    });
  }

  return (
    <div className="flex flex-col gap-4 rounded-lg border-2 border-kabut p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-base font-semibold text-tanah">{lot.nama_petani}</p>
          <p className="text-sm text-tanah/70">
            {lot.nama_komoditas} · komitmen {formatAngka(lot.volume_kg)} kg
          </p>
          {lot.nama_penerima && <p className="text-sm text-tanah/60">Tujuan: {lot.nama_penerima}</p>}
        </div>
        {sudahDitimbang && (
          <span className="inline-flex items-center rounded-full bg-daun px-2.5 py-1 text-sm font-semibold text-kertas">
            Selesai
          </span>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={`berat-${lot.id}`} className="text-base font-medium text-tanah">
          Berat aktual (kg)
        </label>
        <input
          id={`berat-${lot.id}`}
          type="number"
          inputMode="decimal"
          min={0.1}
          step="0.1"
          value={beratAktual}
          onChange={(e) => setBeratAktual(e.target.value)}
          className="angka min-h-sentuh rounded-md border-2 border-kabut bg-kertas px-4 text-lg font-semibold text-tanah focus:border-daun"
        />
      </div>

      <AmbilFoto label="Foto muat" nilai={foto} onUbah={setFoto} />

      <label className="flex min-h-sentuh cursor-pointer items-center gap-3 rounded-md border-2 border-kabut px-4">
        <input
          type="checkbox"
          className="h-6 w-6 shrink-0"
          checked={cacatTerlihat}
          onChange={(e) => setCacatTerlihat(e.target.checked)}
        />
        <span className="text-base font-medium text-tanah">Ada cacat terlihat</span>
      </label>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={`catatan-${lot.id}`} className="text-base font-medium text-tanah">
          Catatan <span className="font-normal text-tanah/60">(opsional)</span>
        </label>
        <textarea
          id={`catatan-${lot.id}`}
          value={catatan}
          onChange={(e) => setCatatan(e.target.value)}
          rows={2}
          className="rounded-md border-2 border-kabut bg-kertas px-4 py-2 text-base text-tanah focus:border-daun"
        />
      </div>

      {gagalMenyimpan && (
        <p role="alert" className="text-sm text-tanah-liat">
          Gagal menyimpan timbangan. Coba lagi.
        </p>
      )}

      <Tombol type="button" varian="aksi" onClick={simpan} disabled={!beratValid || sedangMenyimpan}>
        {sedangMenyimpan ? "Menyimpan…" : sudahDitimbang ? "Perbarui timbangan" : "Simpan timbangan"}
      </Tombol>

      <div className="flex flex-col items-center gap-1 border-t-2 border-kabut pt-4">
        {qrDataUrl && <img src={qrDataUrl} alt={`QR lot ${lot.kode_qr}`} className="h-32 w-32" />}
        <p className="angka text-sm text-tanah/70">{lot.kode_qr}</p>
      </div>
    </div>
  );
}
