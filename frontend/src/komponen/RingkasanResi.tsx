import type { components } from "@/api/client";

type ResiLotRingkasOut = components["schemas"]["ResiLotRingkasOut"];

interface RingkasanResiProps {
  resi: ResiLotRingkasOut[] | undefined;
}

export default function RingkasanResi({ resi }: RingkasanResiProps) {
  if (!resi || resi.length === 0) return null;

  return (
    <div className="flex w-full flex-col gap-1.5 rounded-lg bg-tanah/5 px-3 py-2.5">
      <p className="text-keterangan font-semibold text-tanah/70">Nomor resi</p>
      <ul className="flex flex-col gap-1">
        {resi.map((item) => (
          <li key={item.lot_id} className="angka break-all text-keterangan font-bold text-tanah">
            {item.kode_qr}
          </li>
        ))}
      </ul>
    </div>
  );
}
