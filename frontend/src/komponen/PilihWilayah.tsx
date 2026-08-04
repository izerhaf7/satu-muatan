/** Autocomplete daerah (K14) — desa / kecamatan / kabupaten.
 *
 *  Datanya dari database kita sendiri (6.612 wilayah Jawa Barat, sumber
 *  Kemendagri), jadi daftarnya muncul seketika dan tetap jalan tanpa internet.
 *
 *  Memilih satu daerah mengisi seluruh komponen alamat sekaligus — pola yang
 *  sama dengan aplikasi ojek online: pengguna mengetik sedikit, sistem yang
 *  melengkapi, dan kalau daerah itu punya koordinat, petanya ikut melompat. */

import { useEffect, useRef, useState } from "react";
import { MapPin, Search } from "lucide-react";

import type { components } from "@/api/client";
import { useCariWilayah } from "@/hooks/useAlamat";

type WilayahOut = components["schemas"]["WilayahOut"];

interface PilihWilayahProps {
  label: string;
  id: string;
  /** Teks yang sudah terpilih (jalur lengkap), ditampilkan sebagai nilai awal. */
  nilai: string;
  onPilih: (w: WilayahOut) => void;
}

export default function PilihWilayah({ label, id, nilai, onPilih }: PilihWilayahProps) {
  const [ketikan, setKetikan] = useState("");
  const [terbuka, setTerbuka] = useState(false);
  const wadah = useRef<HTMLDivElement>(null);
  const hasil = useCariWilayah(ketikan);

  // Klik di luar menutup daftar — tanpa ini daftarnya menggantung menutupi
  // isian berikutnya di layar 360px.
  useEffect(() => {
    function diLuar(e: MouseEvent) {
      if (wadah.current && !wadah.current.contains(e.target as Node)) setTerbuka(false);
    }
    document.addEventListener("mousedown", diLuar);
    return () => document.removeEventListener("mousedown", diLuar);
  }, []);

  function pilih(w: WilayahOut) {
    onPilih(w);
    setKetikan("");
    setTerbuka(false);
  }

  const daftar = hasil.data ?? [];

  return (
    <div ref={wadah} className="relative flex flex-col gap-1.5">
      <label htmlFor={id} className="text-keterangan font-semibold text-tanah">
        {label}
      </label>

      <div className="relative">
        <Search
          aria-hidden
          className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-tanah/40"
        />
        <input
          id={id}
          value={ketikan}
          onChange={(e) => {
            setKetikan(e.target.value);
            setTerbuka(true);
          }}
          onFocus={() => setTerbuka(true)}
          placeholder={nilai || "Ketik nama desa / kecamatan"}
          autoComplete="off"
          role="combobox"
          aria-expanded={terbuka && daftar.length > 0}
          aria-controls={`${id}-daftar`}
          className="min-h-sentuh w-full rounded-lg border-2 border-kabut bg-kertas pl-10 pr-4 text-base text-tanah placeholder:text-tanah/40 transition-colors duration-cepat hover:border-tanah/30 focus:border-daun focus:outline-none focus:ring-2 focus:ring-daun/25"
        />
      </div>

      {nilai && !ketikan && (
        <p className="flex items-start gap-1.5 text-keterangan text-tanah/60">
          <MapPin aria-hidden className="mt-0.5 h-3.5 w-3.5 shrink-0 text-daun" />
          {nilai}
        </p>
      )}

      {terbuka && ketikan.trim().length >= 2 && (
        <ul
          id={`${id}-daftar`}
          role="listbox"
          className="absolute top-full z-20 mt-1 max-h-64 w-full overflow-y-auto rounded-lg border-2 border-kabut bg-kertas shadow-sedang"
        >
          {hasil.isLoading && <li className="px-4 py-3 text-keterangan text-tanah/50">Mencari…</li>}
          {!hasil.isLoading && daftar.length === 0 && (
            <li className="px-4 py-3 text-keterangan text-tanah/50">
              Tidak ada daerah yang cocok. Kamu tetap bisa mengetik alamatnya sendiri di bawah.
            </li>
          )}
          {daftar.map((w) => (
            <li key={w.kode}>
              <button
                type="button"
                role="option"
                aria-selected={false}
                onClick={() => pilih(w)}
                className="flex w-full min-h-sentuh flex-col items-start justify-center gap-0.5 px-4 py-2 text-left transition-colors duration-cepat hover:bg-daun/10 focus-visible:bg-daun/10"
              >
                <span className="text-base font-semibold text-tanah">{w.nama}</span>
                <span className="text-keterangan text-tanah/55">{w.jalur}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
