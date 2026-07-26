/** Tombol + dialog konfirmasi "Tutup slot" (§5.4, peran Koperasi). Menetapkan harga
 *  final + jaminan atap, mengunci rencana armada, membuat lot, memesan ke vendor —
 *  aksi tidak bisa dibatalkan makanya wajib konfirmasi. */

import { useState } from "react";

import Dialog from "@/komponen/Dialog";
import Tombol from "@/komponen/Tombol";
import { useTutupSlot } from "@/hooks/useDetailSlot";

interface PanelTutupSlotProps {
  slotId: string;
}

export default function PanelTutupSlot({ slotId }: PanelTutupSlotProps) {
  const [konfirmasi, setKonfirmasi] = useState(false);
  const tutupSlot = useTutupSlot(slotId);

  return (
    <>
      <Tombol type="button" varian="aksi" onClick={() => setKonfirmasi(true)}>
        Tutup slot
      </Tombol>

      <Dialog terbuka={konfirmasi} onTutup={() => setKonfirmasi(false)} judul="Tutup slot ini?">
        <div className="flex flex-col gap-4">
          <p className="text-base text-tanah/80">
            Harga final akan ditetapkan dari volume yang terkumpul sekarang. Petani yang sudah bergabung tidak akan
            ditagih di atas harga atapnya — kalau ada selisih, koperasi yang menanggung. Slot yang sudah ditutup
            tidak bisa dibuka kembali.
          </p>
          {tutupSlot.isError && <p className="text-sm text-tanah-liat">Gagal menutup slot. Coba lagi.</p>}
          <div className="flex flex-col gap-3">
            <Tombol
              type="button"
              varian="aksi"
              disabled={tutupSlot.isPending}
              onClick={() => tutupSlot.mutate(undefined, { onSuccess: () => setKonfirmasi(false) })}
            >
              {tutupSlot.isPending ? "Menutup…" : "Ya, tutup slot"}
            </Tombol>
            <Tombol type="button" varian="sekunder" onClick={() => setKonfirmasi(false)}>
              Batal
            </Tombol>
          </div>
        </div>
      </Dialog>
    </>
  );
}
