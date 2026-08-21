/** Layar Daftar (§9.1 tambahan) — pendaftaran mandiri, tanpa verifikasi OTP
 *  (keputusan produk). Hanya Petani & Penerima; Petugas sengaja tidak ada di
 *  sini (peran paling sensitif — tetap lewat seed/didaftarkan manual). Auto
 *  masuk setelah sukses, sama seperti Masuk.tsx. */

import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ChefHat, Sprout } from "lucide-react";

import type { components } from "@/api/client";
import { ApiError } from "@/api/client";
import InputPin from "@/komponen/InputPin";
import InputTeks from "@/komponen/InputTeks";
import KerangkaAuth from "@/komponen/KerangkaAuth";
import Tombol from "@/komponen/Tombol";
import { useDaftar } from "@/hooks/useAuth";

type PeranDaftar = components["schemas"]["DaftarRequest"]["peran"];

// Sama dengan validasi server (`_POLA_NO_HP` di schemas/auth.py) — diawali 0,
// 9-14 digit total. Difilter saat mengetik supaya huruf tidak bisa masuk sama
// sekali, bukan cuma ditolak belakangan.
const POLA_NO_HP = /^0\d{8,13}$/;

const PILIHAN_PERAN: { peran: PeranDaftar; label: string; keterangan: string; ikon: typeof Sprout }[] = [
  { peran: "PETANI", label: "Petani", keterangan: "Kirim panen", ikon: Sprout },
  { peran: "PENERIMA", label: "Penerima", keterangan: "Terima kiriman", ikon: ChefHat },
];

export default function Daftar() {
  const navigate = useNavigate();
  const [nama, setNama] = useState("");
  const [peran, setPeran] = useState<PeranDaftar>("PETANI");
  const [noHp, setNoHp] = useState("");
  const [pin, setPin] = useState("");
  const [pinKonfirmasi, setPinKonfirmasi] = useState("");
  const daftar = useDaftar();

  const pinTidakSama = pinKonfirmasi.length === 6 && pin !== pinKonfirmasi;
  const noHpTidakValid = noHp.length > 0 && !POLA_NO_HP.test(noHp);
  const bisaDaftar =
    nama.trim().length > 0 && POLA_NO_HP.test(noHp) && pin.length === 6 && pin === pinKonfirmasi;

  function kirim(e: FormEvent) {
    e.preventDefault();
    if (!bisaDaftar) return;
    daftar.mutate(
      { nama, no_hp: noHp, pin, peran },
      { onSuccess: () => navigate("/", { replace: true }) },
    );
  }

  const pesanGalat =
    daftar.isError && daftar.error instanceof ApiError
      ? ((daftar.error.body as { detail?: string } | null)?.detail ?? "Gagal daftar. Coba lagi.")
      : daftar.isError
        ? "Gagal daftar. Coba lagi."
        : null;

  return (
    <KerangkaAuth keterangan="Daftar akun baru untuk mulai mengelola pengiriman">
      <div className="overflow-hidden rounded-xl shadow-lembut">
        <div aria-hidden className="h-1 bg-daun" />
        <form onSubmit={kirim} className="kartu-tonjol flex flex-col gap-4 rounded-t-none border-t-0 p-6">
          <InputTeks
            label="Nama"
            name="nama"
            type="text"
            autoComplete="name"
            placeholder="Nama lengkap"
            value={nama}
            onChange={(e) => setNama(e.target.value)}
            required
          />

          <div className="flex flex-col gap-1.5">
            <span className="text-keterangan font-semibold text-tanah">Daftar sebagai</span>
            <div className="grid grid-cols-2 gap-3">
              {PILIHAN_PERAN.map((p) => {
                const aktif = p.peran === peran;
                return (
                  <button
                    key={p.peran}
                    type="button"
                    onClick={() => setPeran(p.peran)}
                    aria-pressed={aktif}
                    className={`kartu-datar flex min-h-sentuh cursor-pointer flex-col items-center gap-1.5 p-3 text-center transition-colors duration-cepat ${
                      aktif ? "border-daun bg-daun/5" : "hover:border-daun/50"
                    }`}
                  >
                    <span
                      className={`flex h-9 w-9 items-center justify-center rounded-lg ${
                        aktif ? "bg-daun/15 text-daun" : "bg-tanah/5 text-tanah/60"
                      }`}
                    >
                      <p.ikon aria-hidden className="h-4.5 w-4.5" strokeWidth={2} />
                    </span>
                    <span className="text-base font-bold text-tanah">{p.label}</span>
                    <span className="text-keterangan text-tanah/60">{p.keterangan}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <InputTeks
            label="Nomor HP"
            name="no_hp"
            type="tel"
            inputMode="numeric"
            autoComplete="tel"
            placeholder="0812xxxxxxxx"
            value={noHp}
            onChange={(e) => setNoHp(e.target.value.replace(/\D/g, "").slice(0, 14))}
            pesanKesalahan={noHpTidakValid ? "Nomor HP harus diawali 0 dan hanya angka" : undefined}
            required
          />
          <InputPin label="Buat PIN (6 digit)" value={pin} onChange={(e) => setPin(e.target.value)} required />
          <InputPin
            id="pin_konfirmasi"
            name="pin_konfirmasi"
            label="Ulangi PIN"
            value={pinKonfirmasi}
            onChange={(e) => setPinKonfirmasi(e.target.value)}
            pesanKesalahan={pinTidakSama ? "PIN tidak sama" : undefined}
            required
          />
          {pesanGalat && (
            <p role="alert" className="text-sm text-tanah-liat">
              {pesanGalat}
            </p>
          )}
          <Tombol type="submit" varian="aksi" sedangProses={daftar.isPending} disabled={!bisaDaftar}>
            Daftar
          </Tombol>
        </form>
      </div>

      <div className="mx-auto flex flex-col items-center gap-2">
        <Link
          to="/masuk"
          className="text-keterangan font-medium text-daun transition-colors duration-cepat hover:text-tanah"
        >
          Sudah punya akun? Masuk
        </Link>
        <Link
          to="/"
          className="text-keterangan font-medium text-tanah/50 transition-colors duration-cepat hover:text-tanah"
        >
          ← Kembali ke beranda situs
        </Link>
      </div>
    </KerangkaAuth>
  );
}
