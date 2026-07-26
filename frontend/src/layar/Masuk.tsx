/** Layar Masuk (§9.1) — nomor HP + PIN 6 digit, plus panel "Masuk cepat (demo)". */

import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import type { components } from "@/api/client";
import InputPin from "@/komponen/InputPin";
import InputTeks from "@/komponen/InputTeks";
import Tombol from "@/komponen/Tombol";
import { useMasuk, useMasukDemo } from "@/hooks/useAuth";

type AkunDemo = components["schemas"]["AkunDemo"];

const AKUN_DEMO: { akun: AkunDemo; label: string }[] = [
  { akun: "KOPERASI", label: "Pengurus Koperasi" },
  { akun: "PETANI_ASEP", label: "Petani Asep" },
  { akun: "PETANI_WATI", label: "Petani Wati" },
  { akun: "PENERIMA_CIBIRU", label: "Kepala Dapur SPPG Cibiru" },
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
      <div className="flex flex-col gap-1 text-center">
        <h1 className="text-2xl font-bold text-tanah">Satu Muatan</h1>
        <p className="text-base text-tanah/70">Masuk untuk lanjut</p>
      </div>

      <form onSubmit={kirim} className="flex flex-col gap-4">
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
        <Tombol type="submit" varian="aksi" disabled={masuk.isPending}>
          {masuk.isPending ? "Memeriksa…" : "Masuk"}
        </Tombol>
      </form>

      <div className="flex flex-col gap-3 border-t-2 border-kabut pt-6">
        <p className="text-center text-base font-medium text-tanah">Masuk cepat (demo)</p>
        <div className="flex flex-col gap-3">
          {AKUN_DEMO.map((a) => (
            <Tombol
              key={a.akun}
              type="button"
              varian="sekunder"
              disabled={masukDemo.isPending}
              onClick={() => kirimDemo(a.akun)}
            >
              {a.label}
            </Tombol>
          ))}
        </div>
        {masukDemo.isError && (
          <p role="alert" className="text-center text-sm text-tanah-liat">
            Gagal masuk demo. Coba lagi.
          </p>
        )}
      </div>
    </main>
  );
}
