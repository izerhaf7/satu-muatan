/** Fallback statis untuk HeroTiga — dipakai sebagai Suspense fallback SAAT chunk
 *  three.js masih dimuat, dan sebagai pengganti permanen kalau prefers-reduced-motion
 *  aktif atau perangkat tidak punya WebGL. SVG murni, palet sama persis dengan
 *  material HeroTiga (lihat ../palet.ts) supaya transisi poster → 3D tidak melompat. */

import { PALET } from "../palet";

interface PosterTrukProps {
  className?: string;
}

export default function PosterTruk({ className = "" }: PosterTrukProps) {
  return (
    <svg
      viewBox="0 0 420 320"
      className={className}
      role="img"
      aria-label="Ilustrasi truk pikap membawa karung hasil panen"
    >
      <ellipse cx="205" cy="270" rx="150" ry="18" fill={PALET.tanah} opacity="0.12" />

      {/* daun mengambang di atas bak */}
      <g transform="translate(255 78) rotate(-18)">
        <path d="M0 18 C 4 2, 22 -8, 40 0 C 30 14, 12 20, 0 18 Z" fill={PALET.daun} />
        <line x1="0" y1="18" x2="-14" y2="26" stroke={PALET.daun} strokeWidth="2" strokeLinecap="round" />
      </g>

      {/* roda */}
      <circle cx="118" cy="238" r="26" fill={PALET.tanah} />
      <circle cx="118" cy="238" r="9" fill={PALET.kabut} />
      <circle cx="296" cy="238" r="26" fill={PALET.tanah} />
      <circle cx="296" cy="238" r="9" fill={PALET.kabut} />

      {/* rangka bawah */}
      <rect x="70" y="212" width="290" height="16" rx="3" fill={PALET.tanah} />

      {/* kabin */}
      <g>
        <polygon points="72,212 72,120 150,104 176,120 176,212" fill={PALET.daun} />
        <polygon points="72,120 150,104 176,120 150,132" fill={PALET.daun} opacity="0.75" />
        <rect x="90" y="128" width="52" height="46" rx="4" fill={PALET.kabut} />
      </g>

      {/* bak terbuka */}
      <g>
        <polygon points="182,212 182,140 352,140 352,212" fill={PALET.kertas} stroke={PALET.kabut} strokeWidth="2" />
        <polygon points="182,140 352,140 352,128 182,128" fill={PALET.kertas} opacity="0.85" stroke={PALET.kabut} strokeWidth="1.5" />
        <rect x="336" y="132" width="16" height="80" fill={PALET.kertas} opacity="0.9" stroke={PALET.kabut} strokeWidth="1.5" />
      </g>

      {/* karung di dalam bak */}
      <g>
        <rect x="206" y="150" width="44" height="62" rx="20" fill={PALET.tanah} />
        <path d="M212 150 q16 -10 32 0" fill="none" stroke={PALET.kertas} strokeWidth="2.5" strokeLinecap="round" />
        <rect x="252" y="158" width="44" height="54" rx="20" fill={PALET.tanah} opacity="0.92" />
        <path d="M258 158 q16 -10 32 0" fill="none" stroke={PALET.kertas} strokeWidth="2.5" strokeLinecap="round" />
        <rect x="230" y="168" width="40" height="44" rx="18" fill={PALET.tanah} opacity="0.8" />
      </g>
    </svg>
  );
}
