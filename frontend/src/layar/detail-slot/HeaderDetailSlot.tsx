/** Header Detail Slot (§9.4) — kode slot, ringkasan rute, status, hitung mundur cutoff.
 *  Dibangun di atas HeaderLayar (kerangka) supaya sticky + tombol kembali seragam
 *  dengan layar lain (§K12). */

import BadgeStatus from "@/komponen/BadgeStatus";
import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import type { components } from "@/api/client";
import HitungMundur from "@/komponen/HitungMundur";
import { formatAngka } from "@/utils/format";

type SlotDetailOut = components["schemas"]["SlotDetailOut"];

interface HeaderDetailSlotProps {
  slot: SlotDetailOut;
}

export default function HeaderDetailSlot({ slot }: HeaderDetailSlotProps) {
  const asal = slot.titik_kumpul.kecamatan ?? slot.titik_kumpul.desa ?? slot.titik_kumpul.nama;
  const jumlahTujuan = slot.tujuan.length;

  return (
    <div className="flex flex-col gap-3">
      <HeaderLayar
        judul={slot.kode}
        subjudul={`${asal} → ${jumlahTujuan} tujuan · ${formatAngka(slot.jarak_km)} km`}
        kembaliKe="/beranda"
        aksi={<BadgeStatus status={slot.status} />}
      />
      {slot.status === "DIBUKA" && <HitungMundur cutoffAt={slot.cutoff_at} waktuServer={slot.waktu_server} />}
    </div>
  );
}
