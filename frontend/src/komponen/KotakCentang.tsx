/** Checkbox berlabel — baris target sentuh 48px penuh (bukan cuma kotaknya),
 *  dengan baris keterangan opsional di bawah label (mis. penjelasan singkat). */

import { forwardRef, type InputHTMLAttributes } from "react";

interface KotakCentangProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  keterangan?: string;
}

const KotakCentang = forwardRef<HTMLInputElement, KotakCentangProps>(
  ({ label, keterangan, id, name, className = "", ...props }, ref) => {
    const inputId = id ?? name ?? label.toLowerCase().replace(/\s+/g, "-");
    return (
      <label
        htmlFor={inputId}
        className="-mx-2 flex min-h-sentuh cursor-pointer items-center gap-3 rounded-lg px-2 transition-colors duration-cepat hover:bg-tanah/5 active:bg-tanah/10"
      >
        <input
          ref={ref}
          type="checkbox"
          id={inputId}
          name={name}
          className={`h-6 w-6 shrink-0 accent-daun ${className}`}
          {...props}
        />
        <span className="flex flex-col">
          <span className="text-base text-tanah">{label}</span>
          {keterangan && <span className="text-keterangan text-tanah/60">{keterangan}</span>}
        </span>
      </label>
    );
  },
);
KotakCentang.displayName = "KotakCentang";

export default KotakCentang;
