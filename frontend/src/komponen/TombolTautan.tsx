/** Kembar Tombol untuk navigasi (<Link>) — gaya identik, semantik tautan.
 *  Menggantikan kelas tombol yang selama ini disalin-tempel di 5 tempat. */

import { Link, type LinkProps } from "react-router-dom";
import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";

import { kelasDasarTombol, kelasVarianTombol, type VarianTombol } from "./Tombol";

interface TombolTautanProps extends LinkProps {
  varian?: VarianTombol;
  children: ReactNode;
  ikon?: LucideIcon;
}

export default function TombolTautan({
  varian = "aksi",
  className = "",
  children,
  ikon: Ikon,
  ...props
}: TombolTautanProps) {
  return (
    <Link className={`${kelasDasarTombol} ${kelasVarianTombol[varian]} ${className}`} {...props}>
      {Ikon && <Ikon aria-hidden className="h-5 w-5" strokeWidth={2.25} />}
      {children}
    </Link>
  );
}
