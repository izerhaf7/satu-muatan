/** Select berlabel — kembaran InputTeks untuk elemen <select>, dengan chevron
 *  kustom (lucide) karena panah bawaan browser dimatikan lewat appearance-none. */

import { forwardRef, type SelectHTMLAttributes } from "react";
import { ChevronDown } from "lucide-react";

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  pesanKesalahan?: string;
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, id, name, pesanKesalahan, className = "", children, ...props }, ref) => {
    const selectId = id ?? name ?? label.toLowerCase().replace(/\s+/g, "-");
    return (
      <div className="flex flex-col gap-1.5">
        <label htmlFor={selectId} className="text-keterangan font-semibold text-tanah">
          {label}
        </label>
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            name={name}
            className={`min-h-sentuh w-full appearance-none rounded-lg border-2 border-kabut bg-kertas px-4 pr-11 text-base text-tanah transition-colors duration-cepat hover:border-tanah/30 focus:border-daun focus:outline-none focus:ring-2 focus:ring-daun/25 disabled:cursor-not-allowed disabled:border-kabut disabled:bg-kabut/30 disabled:text-tanah/40 ${className}`}
            aria-invalid={pesanKesalahan ? true : undefined}
            {...props}
          >
            {children}
          </select>
          <ChevronDown
            aria-hidden
            className="pointer-events-none absolute right-4 top-1/2 h-5 w-5 -translate-y-1/2 text-tanah/50"
          />
        </div>
        {pesanKesalahan && (
          <p role="alert" className="text-keterangan font-medium text-tanah-liat">
            {pesanKesalahan}
          </p>
        )}
      </div>
    );
  },
);
Select.displayName = "Select";

export default Select;
