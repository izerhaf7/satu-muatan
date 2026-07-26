/** Ambil foto — input kamera (dengan fallback file picker) + pratinjau + kompresi client
 *  ke <=800px JPEG (spec §3.1). Dipakai layar Muat (§9.5, foto muat) dan Serah Terima
 *  (§9.7, foto bongkar opsional). Target sentuh >=48px. */

import { useId, useRef, useState } from "react";

import { kompresiFoto } from "@/utils/kompresiFoto";

interface AmbilFotoProps {
  label: string;
  nilai: string | null;
  onUbah: (dataUrlBase64: string | null) => void;
  wajib?: boolean;
  className?: string;
}

export default function AmbilFoto({ label, nilai, onUbah, wajib = false, className = "" }: AmbilFotoProps) {
  const [memproses, setMemproses] = useState(false);
  const [kesalahan, setKesalahan] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  // useId() (bukan turunan dari `label`) — beberapa kartu lot menampilkan AmbilFoto
  // dengan label yang sama ("Foto muat") pada satu halaman; id per-instance harus unik.
  const inputId = `foto-${useId()}`;

  async function tanganiPilihBerkas(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setMemproses(true);
    setKesalahan(null);
    try {
      const dataUrl = await kompresiFoto(file);
      onUbah(dataUrl);
    } catch (err) {
      setKesalahan(err instanceof Error ? err.message : "Gagal memproses foto.");
    } finally {
      setMemproses(false);
      // Reset value supaya memilih berkas yang sama dua kali tetap memicu onChange.
      e.target.value = "";
    }
  }

  function hapusFoto() {
    onUbah(null);
  }

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      <p className="text-base font-medium text-tanah">
        {label}
        {wajib && <span className="text-tanah-liat"> *</span>}
      </p>

      {nilai ? (
        <div className="flex flex-col items-start gap-2">
          <img
            src={nilai}
            alt={`Pratinjau ${label.toLowerCase()}`}
            className="max-h-48 w-auto rounded-md border-2 border-kabut object-cover"
          />
          <button
            type="button"
            onClick={hapusFoto}
            className="inline-flex min-h-sentuh items-center justify-center rounded-md border-2 border-tanah px-4 text-base font-semibold text-tanah"
          >
            Ganti foto
          </button>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={memproses}
          className="inline-flex min-h-sentuh items-center justify-center gap-2 rounded-md border-2 border-dashed border-kabut px-4 text-base font-semibold text-tanah disabled:opacity-60"
        >
          {memproses ? "Memproses foto…" : "Ambil foto"}
        </button>
      )}

      {/* capture="environment" mengarahkan ke kamera belakang di HP; di desktop/tanpa
          kamera browser otomatis jatuh ke file picker biasa — tetap berfungsi (gate demo). */}
      <input
        ref={inputRef}
        id={inputId}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={tanganiPilihBerkas}
        className="hidden"
      />

      {kesalahan && (
        <p role="alert" className="text-sm text-tanah-liat">
          {kesalahan}
        </p>
      )}
    </div>
  );
}
