/** Nilai hex mentah dari palet 5 warna (spec §10 / tailwind.config.js), untuk konteks yang
 *  tidak bisa memakai kelas Tailwind — SVG fallback (PosterTruk) dan material three.js
 *  (HeroTiga). SATU sumber kebenaran supaya keduanya tidak pernah drift dari tema. */
export const PALET = {
  tanah: "#2B2119",
  kertas: "#FAF7F2",
  daun: "#2F6B3A",
  tanahLiat: "#C1502E",
  kabut: "#D8D2C7",
} as const;
