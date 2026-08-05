/** Input teks dasar design system — min-h 48px, label wajib (aksesibilitas). */

import { forwardRef, type InputHTMLAttributes } from "react";

interface InputTeksProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  penanda?: "Wajib" | "Opsional";
  pesanKesalahan?: string;
}

const InputTeks = forwardRef<HTMLInputElement, InputTeksProps>(
  ({ label, penanda, id, name, pesanKesalahan, className = "", ...props }, ref) => {
    const inputId = id ?? name ?? label.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flex-col gap-1.5">
        <label htmlFor={inputId} className="text-keterangan font-semibold text-tanah">
          <span>{label}</span>
          {penanda && <span className="ml-2 font-medium text-tanah/55">{penanda}</span>}
        </label>
        <input
          ref={ref}
          id={inputId}
          name={name}
          className={`min-h-sentuh rounded-lg border-2 border-kabut bg-kertas px-4 text-base text-tanah placeholder:text-tanah/40 transition-colors duration-cepat hover:border-tanah/30 focus:border-daun focus:outline-none focus:ring-2 focus:ring-daun/25 disabled:cursor-not-allowed disabled:border-kabut disabled:bg-kabut/30 disabled:text-tanah/40 ${className}`}
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
InputTeks.displayName = "InputTeks";

export default InputTeks;
