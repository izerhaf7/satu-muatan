/** Primitif tabel data — dipakai layar yang menampilkan tabel (Tier Kendaraan,
 *  Rincian Ongkos, Tabel Lot BA, dst.), menggantikan `Th`/`Td` yang selama ini
 *  disalin-tempel di tiap layar. `Tabel` = bungkus overflow-x + kartu-datar,
 *  `Thead`/`Th` = kepala kolom, `Td` = sel data. Baris terakhir otomatis tanpa
 *  garis bawah lewat varian arbitrer pada elemen `<table>`. */

import type { HTMLAttributes, TableHTMLAttributes, TdHTMLAttributes, ThHTMLAttributes } from "react";

export function Tabel({ children, className = "", ...props }: TableHTMLAttributes<HTMLTableElement>) {
  return (
    <div className="overflow-x-auto kartu-datar">
      <table
        className={`w-full border-collapse text-left [&_tbody_tr:last-child_td]:border-b-0 ${className}`}
        {...props}
      >
        {children}
      </table>
    </div>
  );
}

export function Thead({ children, className = "", ...props }: HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead className={className} {...props}>
      {children}
    </thead>
  );
}

export function Th({ children, className = "", ...props }: ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={`bg-tanah/5 p-2.5 text-left text-keterangan font-bold uppercase tracking-wide text-tanah/70 ${className}`}
      {...props}
    >
      {children}
    </th>
  );
}

export function Td({ children, className = "", ...props }: TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={`border-b border-kabut/60 p-2.5 text-base text-tanah ${className}`} {...props}>
      {children}
    </td>
  );
}
