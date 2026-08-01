/** Tabel lot Berita Acara (§9.8): petani, komoditas, volume vs berat timbang, cacat,
 *  foto muat & bongkar, keputusan serah terima + persen potongan, atribusi + penjelasan. */

import { Tabel, Td, Th, Thead } from "@/komponen/Tabel";
import type { components } from "@/api/client";
import { formatAngka } from "@/utils/format";

import FotoBukti from "./FotoBukti";

type LotBeritaOut = components["schemas"]["LotBeritaOut"];
type KeputusanSerahTerima = components["schemas"]["KeputusanSerahTerima"];
type Atribusi = components["schemas"]["Atribusi"];

const labelKeputusan: Record<KeputusanSerahTerima, string> = {
  TERIMA: "Terima",
  POTONG: "Potong",
  TOLAK: "Tolak",
};

const labelAtribusi: Record<Atribusi, string> = {
  PETANI: "Petani",
  LOGISTIK: "Logistik",
  TIDAK_TERBUKTI: "Tidak terbukti",
  NORMAL: "Normal",
};

interface TabelLotProps {
  lot: LotBeritaOut[];
}

export default function TabelLot({ lot }: TabelLotProps) {
  return (
    <section aria-label="Daftar lot" className="flex flex-col gap-2">
      <h2 className="text-base font-semibold text-tanah">Daftar lot</h2>
      <Tabel className="min-w-[720px] text-sm">
        <Thead>
          <tr>
            <Th>Petani</Th>
            <Th>Komoditas</Th>
            <Th className="text-right">Volume komitmen</Th>
            <Th className="text-right">Berat timbang</Th>
            <Th>Cacat terlihat</Th>
            <Th>Foto muat</Th>
            <Th>Foto bongkar</Th>
            <Th>Keputusan</Th>
            <Th>Atribusi</Th>
          </tr>
        </Thead>
        <tbody>
          {lot.map(({ lot: l, serah_terima }) => (
            <tr key={l.id}>
              <Td>{l.nama_petani}</Td>
              <Td>{l.nama_komoditas}</Td>
              <Td className="angka text-right">{formatAngka(l.volume_kg)} kg</Td>
              <Td className="angka text-right">
                {l.berat_aktual_kg !== null && l.berat_aktual_kg !== undefined
                  ? `${formatAngka(l.berat_aktual_kg)} kg`
                  : "—"}
              </Td>
              <Td>{l.cacat_terlihat ? "Ada" : "Tidak ada"}</Td>
              <Td>
                <FotoBukti base64={l.foto_muat} alt={`Foto muat lot ${l.nama_petani}`} />
              </Td>
              <Td>
                <FotoBukti base64={serah_terima?.foto_bongkar ?? null} alt={`Foto bongkar lot ${l.nama_petani}`} />
              </Td>
              <Td>
                {serah_terima ? (
                  <>
                    {labelKeputusan[serah_terima.keputusan]}
                    {serah_terima.keputusan === "POTONG" && (
                      <span className="angka text-tanah/70"> {serah_terima.persen_potongan}%</span>
                    )}
                  </>
                ) : (
                  <span className="text-tanah/50">Belum serah terima</span>
                )}
              </Td>
              <Td>
                {serah_terima ? (
                  <div className="flex flex-col gap-0.5">
                    <span className="font-medium">{labelAtribusi[serah_terima.atribusi]}</span>
                    <span className="text-xs text-tanah/60">{serah_terima.penjelasan}</span>
                  </div>
                ) : (
                  <span className="text-tanah/50">—</span>
                )}
              </Td>
            </tr>
          ))}
        </tbody>
      </Tabel>
    </section>
  );
}
