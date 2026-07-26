/** Slider bernilai — track & thumb kustom (aksen daun) lintas-browser lewat
 *  varian arbitrer Tailwind untuk pseudo-elemen WebKit/Firefox. Nilai kini
 *  ditampilkan sebagai chip `.angka` di sisi label. */

import type { ChangeEvent } from "react";

interface PenggeserProps {
  label: string;
  value: number;
  onChange: (e: ChangeEvent<HTMLInputElement>) => void;
  min?: number;
  max?: number;
  step?: number;
  /** Satuan ditampilkan setelah angka di chip, mis. "%", "kg". */
  satuan?: string;
  id?: string;
  name?: string;
  className?: string;
}

const kelasSlider =
  "h-2 w-full cursor-pointer appearance-none rounded-full bg-kabut accent-daun outline-none transition-colors duration-cepat " +
  "[&::-webkit-slider-runnable-track]:h-2 [&::-webkit-slider-runnable-track]:rounded-full [&::-webkit-slider-runnable-track]:bg-kabut " +
  "[&::-moz-range-track]:h-2 [&::-moz-range-track]:rounded-full [&::-moz-range-track]:bg-kabut " +
  "[&::-webkit-slider-thumb]:-mt-2 [&::-webkit-slider-thumb]:h-6 [&::-webkit-slider-thumb]:w-6 [&::-webkit-slider-thumb]:appearance-none " +
  "[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-kertas " +
  "[&::-webkit-slider-thumb]:bg-daun [&::-webkit-slider-thumb]:shadow-lembut " +
  "[&::-moz-range-thumb]:h-6 [&::-moz-range-thumb]:w-6 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-2 " +
  "[&::-moz-range-thumb]:border-kertas [&::-moz-range-thumb]:bg-daun [&::-moz-range-thumb]:shadow-lembut";

export default function Penggeser({
  label,
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  satuan,
  id,
  name,
  className = "",
}: PenggeserProps) {
  const inputId = id ?? name ?? label.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-3">
        <label htmlFor={inputId} className="text-keterangan font-semibold text-tanah">
          {label}
        </label>
        <span className="angka inline-flex items-center rounded-full bg-tanah/5 px-2.5 py-0.5 text-keterangan font-semibold text-tanah">
          {value}
          {satuan && <span className="ml-0.5 text-tanah/60">{satuan}</span>}
        </span>
      </div>
      <input
        id={inputId}
        name={name}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={onChange}
        className={`${kelasSlider} ${className}`}
      />
    </div>
  );
}
