/** Satu baris tabel Konfigurasi (§9.9) — label, nilai terformat, satuan, sumber,
 *  catatan sumber (expandable), dan edit inline sesuai tipe (INT/FLOAT/BOOL/STRING).
 *  Sukses PATCH memicu invalidasi query global di `useUbahKonfigurasi` (§9.9:
 *  "ubah angka di sini, angka di layar lain ikut berubah") + banner konfirmasi
 *  lewat `onTersimpan`. */

import { useState, type FormEvent } from "react";

import BadgeSumber from "@/komponen/BadgeSumber";
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
    <li className="flex flex-col gap-2 border-b border-kabut py-3 last:border-0">
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-0.5">
          <p className="text-base font-medium text-tanah">{item.label}</p>
          {!mengedit && <p className="angka text-lg font-semibold text-tanah">{tampilanNilai(item)}</p>}
        </div>
        <div className="flex flex-col items-end gap-2">
          <BadgeSumber status={item.status_sumber} />
          {!mengedit && (
            <Tombol varian="sekunder" className="px-3 text-sm" onClick={bukaEdit}>
              Ubah
            </Tombol>
          )}
        </div>
      </div>

      {item.catatan_sumber && (
        <details className="text-sm text-tanah/60">
          <summary className="inline-block cursor-pointer select-none py-1">Sumber</summary>
          <p className="mt-1 pl-1 text-tanah/70">{item.catatan_sumber}</p>
        </details>
      )}

      {mengedit && (
        <form onSubmit={submitEdit} className="flex flex-col gap-3 rounded-md border-2 border-kabut p-3">
          {item.tipe === "BOOL" ? (
            <label className="flex min-h-sentuh items-center gap-3 text-base text-tanah">
              <input
                type="checkbox"
                checked={boolEdit}
                onChange={(e) => setBoolEdit(e.target.checked)}
                className="h-6 w-6 accent-daun"
              />
              {boolEdit ? "Aktif" : "Nonaktif"}
            </label>
          ) : (
            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-medium text-tanah">
                Nilai baru{item.satuan ? ` (${item.satuan})` : ""}
              </span>
              <input
                type={item.tipe === "INT" || item.tipe === "FLOAT" ? "number" : "text"}
                inputMode={item.tipe === "INT" ? "numeric" : item.tipe === "FLOAT" ? "decimal" : undefined}
                step={item.tipe === "FLOAT" ? "any" : undefined}
                value={nilaiEdit}
                onChange={(e) => setNilaiEdit(e.target.value)}
                className="min-h-sentuh rounded-md border-2 border-kabut bg-kertas px-4 text-base text-tanah focus:border-daun"
              />
            </label>
          )}

          <div className="flex items-center gap-2">
            <Tombol type="submit" disabled={mutasi.isPending}>
              {mutasi.isPending ? "Menyimpan…" : "Simpan"}
            </Tombol>
            <Tombol type="button" varian="sekunder" onClick={batalEdit}>
              Batal
            </Tombol>
          </div>

          {pesanKesalahan && (
            <p role="alert" className="text-sm text-tanah-liat">
              {pesanKesalahan}
            </p>
          )}
        </form>
      )}
    </li>
  );
}
