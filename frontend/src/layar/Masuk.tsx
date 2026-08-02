/** Layar Masuk (§9.1) — nomor HP + PIN 6 digit, plus panel "Masuk cepat (demo)".
 *  Rombak visual Fase 2.6 (K12): tetap layar aplikasi, TANPA animasi dekoratif —
 *  hanya micro-feedback interaksi standar (hover/active/focus, spinner sedangProses)
 *  yang sudah diizinkan di seluruh app. Logika (hook, error, redirect) tidak diubah. */

import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ChefHat, type LucideIcon, Sprout, Warehouse } from "lucide-react";

import type { components } from "@/api/client";
import InputPin from "@/komponen/InputPin";
import InputTeks from "@/komponen/InputTeks";
import Tombol from "@/komponen/Tombol";
import { useMasuk, useMasukDemo } from "@/hooks/useAuth";

type AkunDemo = components["schemas"]["AkunDemo"];

const AKUN_DEMO: { akun: AkunDemo; nama: string; peran: string; ikon: LucideIcon }[] = [
  { akun: "PETUGAS", nama: "Asep", peran: "Petugas Titik Kumpul", ikon: Warehouse },
  { akun: "PETANI_WATI", nama: "Wati", peran: "Petani", ikon: Sprout },
  { akun: "PETANI_DEDI", nama: "Dedi", peran: "Petani", ikon: Sprout },
  { akun: "PENERIMA_CIBIRU", nama: "Bu Rina", peran: "Kepala Dapur Katering Cibiru", ikon: ChefHat },
];

export default function Masuk() {
  const navigate = useNavigate();
  const [noHp, setNoHp] = useState("");
  const [pin, setPin] = useState("");
  const masuk = useMasuk();
  const masukDemo = useMasukDemo();

  function kirim(e: FormEvent) {
    e.preventDefault();
    masuk.mutate(
      { no_hp: noHp, pin },
      { onSuccess: () => navigate("/", { replace: true }) },
    );
  }

  function kirimDemo(akun: AkunDemo) {
    masukDemo.mutate({ akun }, { onSuccess: () => navigate("/", { replace: true }) });
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-8 px-5 py-10">
      <div className="flex flex-col items-center gap-2 text-center">
        <img src="/ikon-192.png" alt="" className="h-14 w-14 rounded-2xl" />
        <p className="text-subjudul font-extrabold text-tanah">Satu Muatan</p>
        <p className="text-keterangan text-tanah/60">Masuk untuk lanjut mengelola pengiriman</p>
      </div>

      <form onSubmit={kirim} className="kartu-tonjol flex flex-col gap-4 p-6">
        <InputTeks
          label="Nomor HP"
          name="no_hp"
          type="tel"
          inputMode="numeric"
          autoComplete="tel"
          placeholder="0812xxxxxxxx"
          value={noHp}
          onChange={(e) => setNoHp(e.target.value)}
          required
        />
        <InputPin value={pin} onChange={(e) => setPin(e.target.value)} required />
        {masuk.isError && (
          <p role="alert" className="text-sm text-tanah-liat">
            Nomor HP atau PIN salah. Coba lagi.
          </p>
        )}
        <Tombol type="submit" varian="aksi" sedangProses={masuk.isPending}>
          Masuk
        </Tombol>
      </form>

      <div className="flex flex-col gap-3">
        <p className="text-center text-base font-medium text-tanah">Masuk cepat (demo)</p>
        <div className="grid grid-cols-2 gap-3">
          {AKUN_DEMO.map((a) => (
            <button
              key={a.akun}
              type="button"
              disabled={masukDemo.isPending}
              onClick={() => kirimDemo(a.akun)}
              className="kartu-datar flex flex-col items-center gap-2 p-4 text-center transition-colors duration-cepat hover:border-daun disabled:cursor-not-allowed disabled:opacity-50"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-daun/10 text-daun">
                <a.ikon aria-hidden className="h-5 w-5" strokeWidth={2} />
              </span>
              <span className="text-base font-bold text-tanah">{a.nama}</span>
              <span className="text-keterangan text-tanah/60">{a.peran}</span>
            </button>
          ))}
        </div>
        {masukDemo.isError && (
          <p role="alert" className="text-center text-sm text-tanah-liat">
            Gagal masuk demo. Coba lagi.
          </p>
        )}
      </div>

      <Link
        to="/"
        className="mx-auto text-keterangan font-medium text-tanah/50 transition-colors duration-cepat hover:text-tanah"
      >
        ← Kembali ke beranda situs
      </Link>
    </main>
  );
}
