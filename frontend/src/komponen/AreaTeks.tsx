/** Textarea berlabel — kembaran InputTeks untuk teks panjang (catatan, alasan). */

import { forwardRef, type TextareaHTMLAttributes } from "react";

interface AreaTeksProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  pesanKesalahan?: string;
}

const AreaTeks = forwardRef<HTMLTextAreaElement, AreaTeksProps>(
  ({ label, id, name, pesanKesalahan, className = "", rows = 3, ...props }, ref) => {
    const areaId = id ?? name ?? label.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flex-col gap-1.5">
        <label htmlFor={areaId} className="text-keterangan font-semibold text-tanah">
          {label}
        </label>
        <textarea
          ref={ref}
          id={areaId}
          name={name}
          rows={rows}
          className={`rounded-lg border-2 border-kabut bg-kertas px-4 py-3 text-base text-tanah placeholder:text-tanah/40 transition-colors duration-cepat hover:border-tanah/30 focus:border-daun focus:outline-none focus:ring-2 focus:ring-daun/25 disabled:cursor-not-allowed disabled:border-kabut disabled:bg-kabut/30 disabled:text-tanah/40 ${className}`}
          aria-invalid={pesanKesalahan ? true : undefined}
          {...props}
        />
        {pesanKesalahan && (
          <p role="alert" className="text-keterangan font-medium text-tanah-liat">
            {pesanKesalahan}
          </p>
        )}
      </div>
    );
  },
);
AreaTeks.displayName = "AreaTeks";

export default AreaTeks;
