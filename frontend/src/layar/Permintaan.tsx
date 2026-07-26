/** Layar Permintaan (§9.7 alur Penerima) — daftar permintaan sendiri + form buat baru.
 *  Varian Koperasi: daftar baca-saja permintaan terbuka (API sudah men-scope otomatis, K6). */

import { useState } from "react";

import KeadaanKosong from "@/komponen/KeadaanKosong";
import Tombol from "@/komponen/Tombol";
import { useDaftarPermintaan } from "@/hooks/usePermintaan";
import { useAuthStore } from "@/stores/authStore";

import FormPermintaan from "./permintaan/FormPermintaan";
import KartuPermintaan from "./permintaan/KartuPermintaan";

export default function Permintaan() {
  const pengguna = useAuthStore((s) => s.pengguna);
  const isPenerima = pengguna?.peran === "PENERIMA";

  const [formTerbuka, setFormTerbuka] = useState(false);
  const daftarPermintaan = useDaftarPermintaan();

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col gap-6 px-5 py-6 pb-24">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-tanah">Permintaan</h1>
        <p className="text-base text-tanah/70">
          {isPenerima ? "Komoditas yang Anda butuhkan" : "Permintaan terbuka dari dapur penerima"}
        </p>
      </header>

      {isPenerima && (
        <>
          {formTerbuka ? (
            <FormPermintaan onSelesai={() => setFormTerbuka(false)} />
          ) : (
            <Tombol varian="aksi" onClick={() => setFormTerbuka(true)}>
              + Buat permintaan baru
            </Tombol>
          )}
        </>
      )}

      <section aria-label="Daftar permintaan" className="flex flex-col gap-3">
        {daftarPermintaan.isLoading && <p className="text-base text-tanah/60">Memuat permintaan…</p>}
        {daftarPermintaan.isError && (
          <div className="flex flex-col items-start gap-3 rounded-lg border-2 border-tanah-liat/40 p-4">
            <p className="text-base text-tanah-liat">Gagal memuat daftar permintaan.</p>
            <Tombol varian="sekunder" onClick={() => daftarPermintaan.refetch()}>
              Coba lagi
            </Tombol>
          </div>
        )}
        {daftarPermintaan.data?.length === 0 &&
          (isPenerima ? (
            <KeadaanKosong
              pesan="Belum ada permintaan. Buat permintaan pertama supaya koperasi tahu kebutuhan Anda."
              teksAksi={formTerbuka ? undefined : "Buat permintaan pertama"}
              onAksi={formTerbuka ? undefined : () => setFormTerbuka(true)}
            />
          ) : (
            <KeadaanKosong pesan="Belum ada permintaan terbuka dari penerima." />
          ))}
        {daftarPermintaan.data?.map((p) => (
          <KartuPermintaan key={p.id} permintaan={p} tampilkanPenerima={!isPenerima} />
        ))}
      </section>
    </main>
  );
}
