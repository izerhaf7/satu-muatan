/** Input teks dasar design system — min-h 48px, label wajib (aksesibilitas). */

import { forwardRef, type InputHTMLAttributes } from "react";

interface InputTeksProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  pesanKesalahan?: string;
}

const InputTeks = forwardRef<HTMLInputElement, InputTeksProps>(
  ({ label, id, name, pesanKesalahan, className = "", ...props }, ref) => {
    const inputId = id ?? name ?? label.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flex-col gap-1.5">
        <label htmlFor={inputId} className="text-base font-medium text-tanah">
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          name={name}
          className={`min-h-sentuh rounded-md border-2 border-kabut bg-kertas px-4 text-base text-tanah placeholder:text-tanah/40 focus:border-daun ${className}`}
          aria-invalid={pesanKesalahan ? true : undefined}
          {...props}
        />
        {pesanKesalahan && (
          <p role="alert" className="text-sm text-tanah-liat">
            {pesanKesalahan}
          </p>
        )}
      </div>
    );
  },
);
InputTeks.displayName = "InputTeks";

export default InputTeks;
