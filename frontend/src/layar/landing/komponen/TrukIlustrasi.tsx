/** Ilustrasi isometrik truk hero — pengganti HeroTiga (three.js, sudah dicabut).
 *  SVG murni + kelas CSS di landing.css (lp-svg-*) yang mereplikasi @keyframes
 *  desain asli (trukBob, bakGoyang, isiPetak, munculHalus, putarRoda, asapNaik).
 *  Semua animasi otomatis nonaktif lewat blok prefers-reduced-motion di landing.css. */

export default function TrukIlustrasi() {
  return (
    <svg
      role="img"
      aria-label="Ilustrasi isometrik truk pengangkut menghadap kanan, bak muatannya terbagi empat petak yang terisi panen empat petani: Asep, Wati, Dedi, Ijah"
      viewBox="0 0 520 300"
      style={{ display: "block", width: "100%", height: "auto", overflow: "visible" }}
    >
      <ellipse cx={252} cy={240} rx={206} ry={12} fill="#0F2D4A" opacity={0.1} />
      <g className="lp-svg-badan">
        <circle cx={122} cy={200} r={16} fill="#0F2D4A" />
        <circle cx={186} cy={200} r={16} fill="#0F2D4A" />
        <circle cx={422} cy={200} r={16} fill="#0F2D4A" />
        <path d="M56 194 H452 V208 H56 Z" fill="#0F2D4A" />
        <g className="lp-svg-bak">
          <path d="M56 84 H296 L332 63 H92 Z" fill="#E8F5EC" stroke="#0F2D4A" strokeWidth={2} strokeLinejoin="round" />
          <rect x={56} y={84} width={240} height={112} fill="#0F2D4A" />
          <g className="lp-svg-bay" style={{ animationDelay: "200ms" }}>
            <rect x={59} y={88} width={55} height={104} fill="#16A34A" />
          </g>
          <g className="lp-svg-bay" style={{ animationDelay: "380ms" }}>
            <rect x={119} y={88} width={55} height={104} fill="#16A34A" />
          </g>
          <g className="lp-svg-bay" style={{ animationDelay: "560ms" }}>
            <rect x={179} y={88} width={55} height={104} fill="#16A34A" />
          </g>
          <g className="lp-svg-bay" style={{ animationDelay: "740ms" }}>
            <rect x={239} y={88} width={55} height={104} fill="#16A34A" />
          </g>
          <g fill="#F5F6F8" fontFamily="'JetBrains Mono', monospace" fontSize={11} fontWeight={700} letterSpacing={1.2} textAnchor="middle">
            <text className="lp-svg-bay-label" style={{ animationDelay: "480ms" }} x={86} y={146}>
              ASEP
            </text>
            <text className="lp-svg-bay-label" style={{ animationDelay: "660ms" }} x={146} y={146}>
              WATI
            </text>
            <text className="lp-svg-bay-label" style={{ animationDelay: "840ms" }} x={206} y={146}>
              DEDI
            </text>
            <text className="lp-svg-bay-label" style={{ animationDelay: "1020ms" }} x={266} y={146}>
              IJAH
            </text>
          </g>
          <path d="M116 88 V192 M176 88 V192 M236 88 V192" stroke="#0F2D4A" strokeWidth={2} />
          <rect x={56} y={84} width={240} height={112} fill="none" stroke="#0F2D4A" strokeWidth={2} />
        </g>
        <path d="M296 104 H392 L428 83 H332 Z" fill="#0F2D4A" />
        <path d="M296 104 H392 L428 83 H332 Z" fill="#F5F6F8" opacity={0.14} />
        <rect x={296} y={104} width={96} height={90} fill="#0F2D4A" />
        <path d="M392 104 L428 83 V175 L392 194 Z" fill="#0F2D4A" />
        <path d="M398 112 L423 97 V133 L398 148 Z" fill="#E8F5EC" opacity={0.92} />
        <path d="M392 150 H440 L476 129 H428 Z" fill="#F5F6F8" opacity={0.16} />
        <rect x={392} y={150} width={48} height={44} fill="#0F2D4A" />
        <path d="M440 150 L476 129 V166 L440 194 Z" fill="#0F2D4A" />
        <path d="M446 160 L470 146 M446 170 L470 156" stroke="#DDE3EA" strokeWidth={2} opacity={0.7} />
        <path d="M296 104 H392 M392 104 V194" stroke="#DDE3EA" strokeWidth={1.5} opacity={0.35} />
        {[
          [104, 208],
          [168, 208],
          [404, 208],
        ].map(([x, y]) => (
          <g key={x} transform={`translate(${x} ${y})`}>
            <g className="lp-svg-roda">
              <circle r={20} fill="#DDE3EA" stroke="#0F2D4A" strokeWidth={2} />
              <path
                d="M-12 0 H12 M0 -12 V12 M-8.5 -8.5 L8.5 8.5 M-8.5 8.5 L8.5 -8.5"
                stroke="#0F2D4A"
                strokeWidth={1.5}
              />
              <circle r={6} fill="#0F2D4A" />
            </g>
          </g>
        ))}
      </g>
      <g className="lp-svg-asap" fill="#DDE3EA">
        <circle cx={50} cy={186} r={5} style={{ animationDelay: "0ms" }} />
        <circle cx={46} cy={188} r={4} style={{ animationDelay: "700ms" }} />
        <circle cx={52} cy={190} r={3} style={{ animationDelay: "1400ms" }} />
      </g>
      <g className="lp-svg-badge">
        <rect x={330} y={20} width={150} height={28} rx={4} fill="none" stroke="#16A34A" strokeWidth={2} />
        <text x={344} y={39} fontFamily="'JetBrains Mono', monospace" fontSize={12} fontWeight={700} letterSpacing={1.6} fill="#16A34A">
          MUATAN PENUH
        </text>
      </g>
    </svg>
  );
}
