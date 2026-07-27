/** Bagian tanda tangan — garis kosong untuk tanda tangan basah saat dicetak
 *  (KEPUTUSAN.md K4). TIDAK ADA capture tanda tangan digital di skema. */

export default function TandaTangan() {
  return (
    <section aria-label="Tanda tangan" className="tanda-tangan flex flex-col gap-6 pt-4">
      <div className="grid grid-cols-2 gap-6">
        <KotakTandaTangan label="Pengurus Koperasi" />
        <KotakTandaTangan label="Penerima" />
      </div>
    </section>
  );
}

function KotakTandaTangan({ label }: { label: string }) {
  return (
    <div className="flex flex-col gap-10">
      <div aria-hidden="true" className="h-16 border-b-2 border-tanah" />
      <p className="text-center text-keterangan font-medium text-tanah">{label}</p>
    </div>
  );
}
