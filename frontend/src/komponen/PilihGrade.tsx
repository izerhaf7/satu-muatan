/** PilihGrade — lima tombol besar berlabel kata untuk grade mutu 1–5 (spec v2 §6.1):
 *  "Sangat baik · Baik · Cukup · Kurang · Tidak layak" — BUKAN angka telanjang.
 *  Dipakai layar Muat (grade_asal, dinilai petugas titik kumpul) dan Serah Terima
 *  (grade_tiba, dinilai penerima). Target sentuh 48px; aksen tanah-liat untuk
 *  grade di bawah ambang standar (Kurang/Tidak layak). */

interface PilihGradeProps {
  label: string;
  nilai: number; // 1..5
  onUbah: (grade: number) => void;
}

const PILIHAN: { grade: number; label: string }[] = [
  { grade: 5, label: "Sangat baik" },
  { grade: 4, label: "Baik" },
  { grade: 3, label: "Cukup" },
  { grade: 2, label: "Kurang" },
  { grade: 1, label: "Tidak layak" },
];

/** Label kata per grade (dipakai juga komponen lain, mis. ringkasan bukti). */
export const LABEL_GRADE: Record<number, string> = Object.fromEntries(PILIHAN.map((p) => [p.grade, p.label]));

export default function PilihGrade({ label, nilai, onUbah }: PilihGradeProps) {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="text-keterangan font-medium text-tanah/80">{label}</legend>
      <div role="radiogroup" aria-label={label} className="grid grid-cols-1 gap-2">
        {PILIHAN.map(({ grade, label: kata }) => {
          const terpilih = nilai === grade;
          const rendah = grade < 3;
          return (
            <button
              key={grade}
              type="button"
              role="radio"
              aria-checked={terpilih}
              onClick={() => onUbah(grade)}
              className={`min-h-sentuh rounded-xl border-2 px-4 text-left text-base font-semibold transition-colors duration-cepat ${
                terpilih
                  ? rendah
                    ? "border-tanah-liat/60 bg-tanah-liat/10 text-tanah-liat"
                    : "border-daun/60 bg-daun/10 text-daun"
                  : "border-kabut bg-kertas text-tanah/70 hover:border-tanah/30 hover:text-tanah"
              }`}
            >
              {kata}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}
