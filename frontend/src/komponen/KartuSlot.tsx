/** Kartu ringkas satu slot — dipakai di daftar Beranda (§9.2). */

import { Link } from "react-router-dom";

import type { components } from "@/api/client";
import { formatAngka, formatTanggal } from "@/utils/format";

import BadgeStatus from "./BadgeStatus";
import BarKapasitas from "./BarKapasitas";
import HitungMundur from "./HitungMundur";

type SlotItemOut = components["schemas"]["SlotItemOut"];

interface KartuSlotProps {
  slot: SlotItemOut;
}

export default function KartuSlot({ slot }: KartuSlotProps) {
  return (
    <Link
      to={`/slot/${slot.id}`}
      className="flex flex-col gap-3 rounded-lg border-2 border-kabut p-4 hover:border-daun focus-visible:border-daun"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="angka text-base font-semibold text-tanah">{slot.kode}</p>
          <p className="text-sm text-tanah/70">
            Kirim {formatTanggal(slot.tanggal_kirim)} · {formatAngka(slot.jarak_km)} km
          </p>
        </div>
        <BadgeStatus status={slot.status} />
      </div>

      {slot.status === "DIBUKA" && <HitungMundur cutoffAt={slot.cutoff_at} cutoffLewat={slot.cutoff_lewat} />}

      <BarKapasitas volumeKg={slot.volume_terkunci_kg} kapasitasKg={slot.kapasitas_rencana_kg ?? null} />

      <p className="text-sm text-tanah/70">{slot.jumlah_petani} petani sudah bergabung</p>
    </Link>
  );
}
