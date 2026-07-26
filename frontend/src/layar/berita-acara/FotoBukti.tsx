/** Thumbnail bukti foto (muat/bongkar) — kecil & ringkas untuk cetak (§9.8).
 *  `base64` disimpan tanpa awalan data URI (kolom TEXT, §12) — ditambahkan di sini.
 *  Gagal decode / tidak ada foto → kotak placeholder, bukan ikon rusak. */

import { useState } from "react";

interface FotoBuktiProps {
  base64: string | null | undefined;
  alt: string;
}

export default function FotoBukti({ base64, alt }: FotoBuktiProps) {
  const [gagal, setGagal] = useState(false);

  if (!base64 || gagal) {
    return (
      <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded border-2 border-dashed border-kabut p-1 text-center text-[10px] leading-tight text-tanah/50">
        Tidak ada foto
      </div>
    );
  }

  const src = base64.startsWith("data:") ? base64 : `data:image/jpeg;base64,${base64}`;

  return (
    <img
      src={src}
      alt={alt}
      onError={() => setGagal(true)}
      className="h-14 w-14 shrink-0 rounded border-2 border-kabut object-cover"
    />
  );
}
