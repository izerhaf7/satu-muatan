/** Dialog dua pilihan saat gabung memicu LUAPAN_KAPASITAS (§5.5, §9.4 butir 5).
 *  Bukan edge case teoretis — terjadi ketika volume baru mendorong H_kasar
 *  melewati atap peserta yang sudah bergabung. Dua jalan keluar:
 *  gabung ke slot berikutnya, atau minta koperasi buka slot kedua.
 *  Logika/hook TIDAK diubah — hanya bahasa tampilan (§K12). */

import { TriangleAlert } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import Dialog from "@/komponen/Dialog";
import Tombol from "@/komponen/Tombol";
import type { LuapanKapasitasOut } from "@/hooks/useGabung";
import { formatRupiah } from "@/utils/format";

interface DialogLuapanKapasitasProps {
  info: LuapanKapasitasOut | null;
  onTutup: () => void;
}

export default function DialogLuapanKapasitas({ info, onTutup }: DialogLuapanKapasitasProps) {
  const navigate = useNavigate();
  const [mintaInfo, setMintaInfo] = useState(false);

  function tutup() {
    setMintaInfo(false);
    onTutup();
  }

  if (!info) return null;

  return (
    <Dialog terbuka={Boolean(info)} onTutup={tutup} judul="Slot ini akan melebihi kapasitas">
      {!mintaInfo ? (
        <div className="flex flex-col gap-4">
          <p className="flex items-start gap-2 text-base text-tanah/80">
            <TriangleAlert aria-hidden className="mt-0.5 h-5 w-5 shrink-0 text-tanah-liat" />
            {info.pesan}
          </p>
          <div className="flex flex-col gap-1.5 rounded-lg bg-tanah-liat/5 p-3.5 text-keterangan text-tanah/80">
            <p>
              Harga berjalan akan naik jadi{" "}
              <span className="angka font-semibold text-tanah">{formatRupiah(info.harga_baru_per_kg)}/kg</span>.
            </p>
            <p>
              Ini memengaruhi harga atap{" "}
              <span className="angka font-semibold text-tanah">{info.jumlah_atap_terdampak}</span> petani yang sudah
              bergabung — koperasi akan menanggung selisihnya.
            </p>
          </div>

          <div className="flex flex-col gap-3">
            <Tombol
              type="button"
              varian="aksi"
              disabled={!info.slot_alternatif_id}
              onClick={() => {
                if (info.slot_alternatif_id) {
                  tutup();
                  navigate(`/slot/${info.slot_alternatif_id}`);
                }
              }}
            >
              Gabung slot berikutnya
            </Tombol>
            {!info.slot_alternatif_id && (
              <p className="text-keterangan text-tanah/60">Belum ada slot berikutnya di hari yang sama.</p>
            )}
            <Tombol type="button" varian="sekunder" onClick={() => setMintaInfo(true)}>
              Minta koperasi buka slot kedua
            </Tombol>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <p className="text-base text-tanah/80">
            Sampaikan ke pengurus koperasi kamu: slot ini sudah penuh, minta dibukakan slot kedua di hari yang sama
            supaya harga atap peserta yang sudah bergabung tetap terjaga.
          </p>
          <Tombol type="button" varian="sekunder" onClick={tutup}>
            Tutup
          </Tombol>
        </div>
      )}
    </Dialog>
  );
}
