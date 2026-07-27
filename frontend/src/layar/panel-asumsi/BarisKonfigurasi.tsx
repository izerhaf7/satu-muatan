/** Satu baris tabel Konfigurasi (§9.9) — label, nilai terformat sebagai chip .angka,
 *  satuan, sumber, catatan sumber (disclosure kustom dengan ChevronDown berputar,
 *  menggantikan marker <details> bawaan), dan edit inline sesuai tipe (INT/FLOAT/BOOL/STRING).
 *  Sukses PATCH memicu invalidasi query global di `useUbahKonfigurasi` (§9.9:
 *  "ubah angka di sini, angka di layar lain ikut berubah") + `onTersimpan` (toast). */

import { useState, type FormEvent } from "react";
import { ChevronDown } from "lucide-react";

import BadgeSumber from "@/komponen/BadgeSumber";
import InputTeks from "@/komponen/InputTeks";
import KotakCentang from "@/komponen/KotakCentang";
import Tombol from "@/komponen/Tombol";
import type { components } from "@/api/client";
import { useUbahKonfigurasi } from "@/hooks/useAsumsi";
import { formatAngka, formatRupiah } from "@/utils/format";

type KonfigurasiOut = components["schemas"]["KonfigurasiOut"];

interface BarisKonfigurasiProps {
  item: KonfigurasiOut;
  onTersimpan: () => void;
}

function nilaiBoolean(nilai: string): boolean {
  return ["true", "1", "ya", "yes", "on"].includes(nilai.trim().toLowerCase());
}

function tampilanNilai(item: KonfigurasiOut): string {
  if (item.tipe === "BOOL") return nilaiBoolean(item.nilai) ? "Aktif" : "Nonaktif";
  if (item.tipe === "STRING") return item.nilai;

  const angka = Number(item.nilai);
  if (Number.isNaN(angka)) return item.nilai;
  if (item.satuan === "Rp") return formatRupiah(angka);
  return item.satuan ? `${formatAngka(angka)} ${item.satuan}` : formatAngka(angka);
}

export default function BarisKonfigurasi({ item, onTersimpan }: BarisKonfigurasiProps) {
  const [mengedit, setMengedit] = useState(false);
  const [sumberTerbuka, setSumberTerbuka] = useState(false);
  const [nilaiEdit, setNilaiEdit] = useState(item.nilai);
  const [boolEdit, setBoolEdit] = useState(() => nilaiBoolean(item.nilai));
  const mutasi = useUbahKonfigurasi();

  function bukaEdit() {
    setNilaiEdit(item.nilai);
    setBoolEdit(nilaiBoolean(item.nilai));
    setMengedit(true);
  }

  function batalEdit() {
    setMengedit(false);
    mutasi.reset();
  }

  function submitEdit(e: FormEvent) {
    e.preventDefault();
    const nilaiBaru = item.tipe === "BOOL" ? String(boolEdit) : nilaiEdit;
    mutasi.mutate(
      { kunci: item.kunci, body: { nilai: nilaiBaru } },
      {
        onSuccess: () => {
          setMengedit(false);
          onTersimpan();
        },
      },
    );
  }

  const pesanKesalahan =
    mutasi.isError && mutasi.error instanceof Error ? "Nilai tidak sesuai — periksa kembali." : null;

  return (
    <li className="flex flex-col gap-2 border-b border-kabut py-3.5 last:border-0">
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1.5">
          <p className="text-base font-medium text-tanah">{item.label}</p>
          {!mengedit && (
            <span className="angka inline-flex w-fit items-center rounded-full bg-tanah/5 px-3 py-1 text-base font-semibold text-tanah">
              {tampilanNilai(item)}
            </span>
          )}
        </div>
        <div className="flex flex-col items-end gap-2">
          <BadgeSumber status={item.status_sumber} />
          {!mengedit && (
            <Tombol varian="sekunder" className="min-h-11 px-3 text-keterangan" onClick={bukaEdit}>
              Ubah
            </Tombol>
          )}
        </div>
      </div>

      {item.catatan_sumber && (
        <div className="text-keterangan text-tanah/60">
          <button
            type="button"
            aria-expanded={sumberTerbuka}
            onClick={() => setSumberTerbuka((v) => !v)}
            className="inline-flex min-h-8 items-center gap-1 py-1 font-semibold text-tanah/70 transition-colors duration-cepat hover:text-tanah"
          >
            <ChevronDown
              aria-hidden
              className={`h-4 w-4 transition-transform duration-cepat ${sumberTerbuka ? "rotate-180" : ""}`}
            />
            Sumber
          </button>
          {sumberTerbuka && <p className="pl-1 text-tanah/70">{item.catatan_sumber}</p>}
        </div>
      )}

      {mengedit && (
        <form onSubmit={submitEdit} className="kartu-datar flex flex-col gap-3 p-3">
          {item.tipe === "BOOL" ? (
            <KotakCentang label={boolEdit ? "Aktif" : "Nonaktif"} checked={boolEdit} onChange={(e) => setBoolEdit(e.target.checked)} />
          ) : (
            <InputTeks
              label={`Nilai baru${item.satuan ? ` (${item.satuan})` : ""}`}
              type={item.tipe === "INT" || item.tipe === "FLOAT" ? "number" : "text"}
              inputMode={item.tipe === "INT" ? "numeric" : item.tipe === "FLOAT" ? "decimal" : undefined}
              step={item.tipe === "FLOAT" ? "any" : undefined}
              value={nilaiEdit}
              onChange={(e) => setNilaiEdit(e.target.value)}
            />
          )}

          <div className="flex items-center gap-2">
            <Tombol type="submit" className="min-h-11 px-4 text-keterangan" sedangProses={mutasi.isPending}>
              Simpan
            </Tombol>
            <Tombol type="button" varian="sekunder" className="min-h-11 px-4 text-keterangan" onClick={batalEdit}>
              Batal
            </Tombol>
          </div>

          {pesanKesalahan && (
            <p role="alert" className="text-keterangan text-tanah-liat">
              {pesanKesalahan}
            </p>
          )}
        </form>
      )}
    </li>
  );
}
