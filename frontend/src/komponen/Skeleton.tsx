/** Skeleton pemuatan — mengganti seluruh teks "Memuat…" polos.
 *  animate-pulse dimatikan otomatis oleh blok reduced-motion global.css. */

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = "" }: SkeletonProps) {
  return <div aria-hidden className={`animate-pulse rounded-lg bg-kabut/60 ${className}`} />;
}

/** Kerangka kartu daftar generik (baris judul + dua baris meta). */
export function SkeletonKartu({ jumlah = 3 }: { jumlah?: number }) {
  return (
    <div role="status" aria-label="Memuat" className="flex flex-col gap-3">
      {Array.from({ length: jumlah }, (_, i) => (
        <div key={i} className="kartu-datar flex flex-col gap-3 p-4">
          <Skeleton className="h-5 w-2/5" />
          <Skeleton className="h-4 w-3/5" />
          <Skeleton className="h-3 w-full" />
        </div>
      ))}
      <span className="sr-only">Memuat…</span>
    </div>
  );
}

/** Kerangka blok angka besar (hero harga / kartu metrik). */
export function SkeletonAngka({ className = "" }: SkeletonProps) {
  return (
    <div role="status" aria-label="Memuat" className={`flex flex-col items-center gap-2 py-4 ${className}`}>
      <Skeleton className="h-4 w-24" />
      <Skeleton className="h-10 w-40" />
      <span className="sr-only">Memuat…</span>
    </div>
  );
}
