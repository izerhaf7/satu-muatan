/** Kartu slot untuk daftar Beranda (§9.2) — pola sama dengan komponen/KartuSlot
 *  (frozen) tapi "diangkat" ke bahasa kartu K12 (kartu-datar) + ikon Users pada
 *  jumlah petani. Dipakai varian Petugas & Petani supaya bahasa kartunya sama. */

import { Users } from "lucide-react";
import { Link } from "react-router-dom";

import BadgeStatus from "@/komponen/BadgeStatus";
import BarKapasitas from "@/komponen/BarKapasitas";
import HitungMundur from "@/komponen/HitungMundur";
import RingkasanResi from "@/komponen/RingkasanResi";
import type { components } from "@/api/client";
import { formatAngka, formatTanggal } from "@/utils/format";

type SlotItemOut = components["schemas"]["SlotItemOut"];

interface KartuSlotDaftarProps {
  slot: SlotItemOut;
}

export default function KartuSlotDaftar({ slot }: KartuSlotDaftarProps) {
  return (
    <Link
      to={`/slot/${slot.id}`}
      className="kartu-datar flex flex-col gap-3 p-4 transition-colors duration-cepat hover:border-daun focus-visible:border-daun"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="angka text-base font-bold text-tanah">{slot.kode}</p>
          <p className="text-keterangan text-tanah/70">
            Kirim {formatTanggal(slot.tanggal_kirim)} · {formatAngka(slot.jarak_km)} km
          </p>
        </div>
        <BadgeStatus status={slot.status} />
      </div>

      {slot.status === "DIBUKA" && <HitungMundur cutoffAt={slot.cutoff_at} cutoffLewat={slot.cutoff_lewat} />}

      <BarKapasitas volumeKg={slot.volume_terkunci_kg} kapasitasKg={slot.kapasitas_rencana_kg ?? null} />

      <p className="inline-flex items-center gap-1.5 text-keterangan text-tanah/70">
        <Users aria-hidden className="h-3.5 w-3.5" />
        {slot.jumlah_petani} petani sudah bergabung
      </p>

      <RingkasanResi resi={slot.resi} />
    </Link>
  );
}
