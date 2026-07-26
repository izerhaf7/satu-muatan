/** Input PIN 6 digit — dipakai layar Masuk (§9.1). Angka besar berjarak, tabular-nums. */

import { forwardRef, type InputHTMLAttributes } from "react";

interface InputPinProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "maxLength" | "inputMode"> {
  label?: string;
  pesanKesalahan?: string;
}

const InputPin = forwardRef<HTMLInputElement, InputPinProps>(
  ({ label = "PIN (6 digit)", id, pesanKesalahan, className = "", ...props }, ref) => {
    const inputId = id ?? "pin";
    return (
      <div className="flex flex-col gap-1.5">
        <label htmlFor={inputId} className="text-keterangan font-semibold text-tanah">
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          name="pin"
          type="password"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={6}
          autoComplete="one-time-code"
          className={`angka min-h-sentuh rounded-lg border-2 border-kabut bg-kertas px-4 text-xl tracking-[0.5em] text-tanah transition-colors duration-cepat hover:border-tanah/30 focus:border-daun focus:outline-none focus:ring-2 focus:ring-daun/25 disabled:cursor-not-allowed disabled:border-kabut disabled:bg-kabut/30 disabled:text-tanah/40 ${className}`}
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
InputPin.displayName = "InputPin";

export default InputPin;
