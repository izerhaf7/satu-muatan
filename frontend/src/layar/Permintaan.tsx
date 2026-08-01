/** Layar Permintaan (§9.7 alur Penerima) — daftar permintaan sendiri + form buat baru.
 *  Varian Koperasi: daftar baca-saja permintaan terbuka (API sudah men-scope otomatis, K6). */

import { useState } from "react";
import { Plus } from "lucide-react";

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import KartuGalat from "@/komponen/KartuGalat";
import KeadaanKosong from "@/komponen/KeadaanKosong";
import { SkeletonKartu } from "@/komponen/Skeleton";
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
    <div className={`flex flex-col gap-6 ${isPenerima ? "lg:grid lg:grid-cols-2 lg:items-start" : ""}`}>
      <div className={isPenerima ? "lg:col-span-2" : undefined}>
        <HeaderLayar
          judul="Permintaan"
          subjudul={isPenerima ? "Komoditas yang Anda butuhkan" : "Permintaan terbuka dari dapur penerima"}
        />
      </div>

      {isPenerima && (
        <>
          {formTerbuka ? (
            <FormPermintaan onSelesai={() => setFormTerbuka(false)} />
          ) : (
            <Tombol varian="aksi" ikon={Plus} onClick={() => setFormTerbuka(true)}>
              Buat permintaan baru
            </Tombol>
          )}
        </>
      )}

      <section
        aria-label="Daftar permintaan"
        className={`flex flex-col gap-3 ${isPenerima ? "" : "lg:grid lg:grid-cols-2 lg:items-start"}`}
      >
        {daftarPermintaan.isLoading && <SkeletonKartu jumlah={3} />}
        {daftarPermintaan.isError && (
          <KartuGalat pesan="Gagal memuat daftar permintaan." onCobaLagi={() => daftarPermintaan.refetch()} />
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
    </div>
  );
}
