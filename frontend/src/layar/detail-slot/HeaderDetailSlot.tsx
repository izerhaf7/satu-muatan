/** Header Detail Slot (§9.4) — kode slot, ringkasan rute, hitung mundur cutoff. */

import BadgeStatus from "@/komponen/BadgeStatus";
import type { components } from "@/api/client";
import HitungMundur from "@/komponen/HitungMundur";
import { formatAngka } from "@/utils/format";

type SlotDetailOut = components["schemas"]["SlotDetailOut"];

interface HeaderDetailSlotProps {
  slot: SlotDetailOut;
}

export default function HeaderDetailSlot({ slot }: HeaderDetailSlotProps) {
  const asal = slot.koperasi.kecamatan ?? slot.koperasi.desa ?? slot.koperasi.nama;
  const jumlahTujuan = slot.tujuan.length;

  return (
    <header className="flex flex-col gap-2">
      <div className="flex items-start justify-between gap-2">
        <p className="angka text-lg font-bold text-tanah">{slot.kode}</p>
        <BadgeStatus status={slot.status} />
      </div>
      <p className="text-base text-tanah/70">
        {asal} → {jumlahTujuan} tujuan · {formatAngka(slot.jarak_km)} km
      </p>
      {slot.status === "DIBUKA" && <HitungMundur cutoffAt={slot.cutoff_at} waktuServer={slot.waktu_server} />}
    </header>
  );
}
