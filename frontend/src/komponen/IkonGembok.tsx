/** Ikon gembok kecil — penanda "harga atap tidak pernah berubah" (§9.4 butir 2,
 *  aturan keras #3). SVG inline, BUKAN emoji (spec §10 melarang emoji di UI).
 *  Dipakai di Detail Slot (kartu Harga Atap) dan Riwayat (kolom atap terkunci). */

interface IkonGembokProps {
  className?: string;
}

export default function IkonGembok({ className = "" }: IkonGembokProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
      className={`inline-block h-4 w-4 shrink-0 ${className}`}
    >
      <rect x="5" y="10.5" width="14" height="10" rx="1.5" stroke="currentColor" strokeWidth="2" />
      <path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="12" cy="15" r="1.6" fill="currentColor" />
    </svg>
  );
}
