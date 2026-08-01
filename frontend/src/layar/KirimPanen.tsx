/** Layar Kirim Panen (spec v2 §3.4) — alur baru petani: masukkan tujuan +
 *  volume + tanggal; sistem menampilkan atap & potensi SEBELUM berkomitmen,
 *  lalu mencocokkan ke muatan. Petani TIDAK memilih slot lagi. */

import { useMemo, useState } from "react";
import { MapPin, PackagePlus, Send, TrendingDown } from "lucide-react";
import { useNavigate } from "react-router-dom";

import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import InputTeks from "@/komponen/InputTeks";
import KartuGalat from "@/komponen/KartuGalat";
import { SkeletonKartu } from "@/komponen/Skeleton";
import Tombol from "@/komponen/Tombol";
import { ApiError } from "@/api/client";
import { useKomoditas } from "@/hooks/useKomoditas";
import { useDaftarPenerima } from "@/hooks/usePenerima";
import { useBuatKiriman, usePratinjauKiriman, type ParamsPratinjau } from "@/hooks/useKiriman";
import { formatRupiah } from "@/utils/format";

function tanggalBesok(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
}

export default function KirimPanen() {
  const navigate = useNavigate();
  const komoditas = useKomoditas();
  const penerima = useDaftarPenerima();
  const buatKiriman = useBuatKiriman();

  const [komoditasId, setKomoditasId] = useState("");
  const [volume, setVolume] = useState("");
  const [tanggal, setTanggal] = useState(tanggalBesok());
  const [penerimaId, setPenerimaId] = useState("");

  const penerimaTerpilih = penerima.data?.find((p) => p.id === penerimaId) ?? null;

  const paramsPratinjau: ParamsPratinjau | null = useMemo(() => {
    const vol = Number(volume);
    if (!penerimaTerpilih || !vol || vol <= 0 || !tanggal) return null;
    return { volumeKg: vol, lat: penerimaTerpilih.lat, lng: penerimaTerpilih.lng, tanggal };
  }, [volume, tanggal, penerimaTerpilih]);

  const pratinjau = usePratinjauKiriman(paramsPratinjau);

  const bisaKirim =
    Boolean(komoditasId) && Number(volume) > 0 && Boolean(tanggal) && penerimaTerpilih !== null && !buatKiriman.isPending;

  async function kirim() {
    if (!bisaKirim || !penerimaTerpilih) return;
    try {
      const hasil = await buatKiriman.mutateAsync({
        komoditas_id: komoditasId,
        volume_kg: Number(volume),
        tanggal_siap: tanggal,
        lat_tujuan: penerimaTerpilih.lat,
        lng_tujuan: penerimaTerpilih.lng,
        alamat_tujuan: penerimaTerpilih.alamat,
      });
      navigate(`/slot/${hasil.slot_id}`);
    } catch {
      /* galat ditampilkan dari buatKiriman.isError di bawah */
    }
  }

  const pesanGalat =
    buatKiriman.isError && buatKiriman.error instanceof ApiError
      ? (buatKiriman.error.body as { detail?: string } | null)?.detail ?? "Gagal mengirim. Coba lagi."
      : buatKiriman.isError
        ? "Gagal mengirim. Coba lagi."
        : null;

  return (
    <div className="flex flex-col gap-6">
      <HeaderLayar judul="Kirim Panen" subjudul="Sistem yang mencocokkan muatan untukmu" kembaliKe="/beranda" />

      <section className="flex flex-col gap-3">
        <label htmlFor="komoditas" className="text-keterangan font-medium text-tanah/80">
          Komoditas
        </label>
        {komoditas.isLoading && <SkeletonKartu />}
        {komoditas.isError && <KartuGalat pesan="Gagal memuat komoditas." onCobaLagi={() => komoditas.refetch()} />}
        {komoditas.data && (
          <div className="grid grid-cols-2 gap-2">
            {komoditas.data.map((k) => (
              <button
                key={k.id}
                type="button"
                onClick={() => setKomoditasId(k.id)}
                className={`min-h-sentuh rounded-xl border-2 px-3 text-left text-base font-semibold transition-colors duration-cepat ${
                  komoditasId === k.id
                    ? "border-daun/60 bg-daun/10 text-daun"
                    : "border-kabut bg-kertas text-tanah/70 hover:border-tanah/30 hover:text-tanah"
                }`}
              >
                {k.nama}
              </button>
            ))}
          </div>
        )}
      </section>

      <div className="grid grid-cols-2 gap-3">
        <InputTeks
          label="Volume (kg)"
          id="volume"
          type="number"
          inputMode="numeric"
          min={1}
          value={volume}
          onChange={(e) => setVolume(e.target.value)}
          className="angka text-lg font-semibold"
        />
        <InputTeks
          label="Tanggal siap"
          id="tanggal"
          type="date"
          value={tanggal}
          onChange={(e) => setTanggal(e.target.value)}
          required
        />
      </div>

      <section className="flex flex-col gap-3">
        <p className="text-keterangan font-medium text-tanah/80">Tujuan</p>
        {penerima.isLoading && <SkeletonKartu />}
        {penerima.isError && <KartuGalat pesan="Gagal memuat daftar tujuan." onCobaLagi={() => penerima.refetch()} />}
        {penerima.data?.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => setPenerimaId(p.id)}
            className={`kartu-datar flex min-h-sentuh items-center gap-3 p-3.5 text-left transition-colors duration-cepat hover:border-daun ${
              penerimaId === p.id ? "border-daun bg-daun/5" : ""
            }`}
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-tanah/5 text-tanah/60">
              <MapPin aria-hidden className="h-4 w-4" />
            </span>
            <span className="flex min-w-0 flex-col">
              <span className="truncate text-base text-tanah">{p.nama}</span>
              <span className="truncate text-keterangan text-tanah/60">{p.alamat}</span>
            </span>
          </button>
        ))}
      </section>

      {paramsPratinjau && pratinjau.data && (
        <section aria-label="Pratinjau harga" className="kartu-hero flex flex-col gap-3 p-5">
          {pratinjau.data.harga_atap_per_kg != null ? (
            <>
              <div className="flex items-baseline justify-between gap-3">
                <p className="text-keterangan font-bold uppercase tracking-wide text-kertas/70">Harga atap kamu</p>
                <p className="angka text-2xl font-bold text-kertas">
                  {formatRupiah(pratinjau.data.harga_atap_per_kg)}<span className="text-base font-semibold">/kg</span>
                </p>
              </div>
              {pratinjau.data.harga_potensial_per_kg != null && (
                <div className="flex items-baseline justify-between gap-3 border-t border-kertas/20 pt-3">
                  <p className="flex items-center gap-1.5 text-keterangan text-kertas/80">
                    <TrendingDown aria-hidden className="h-4 w-4" />
                    {pratinjau.data.slot_cocok_ada ? "Masuk muatan yang ada" : "Kalau ada petani lain searah"}
                  </p>
                  <p className="angka text-xl font-bold text-kertas">
                    ± {formatRupiah(pratinjau.data.harga_potensial_per_kg)}<span className="text-base font-semibold">/kg</span>
                  </p>
                </div>
              )}
              {pratinjau.data.pesan && <p className="text-keterangan text-kertas/70">{pratinjau.data.pesan}</p>}
            </>
          ) : (
            <p className="text-base text-kertas">{pratinjau.data.pesan ?? "Tujuan di luar koridor layanan."}</p>
          )}
        </section>
      )}

      {pesanGalat && (
        <p role="alert" className="text-keterangan text-tanah-liat">
          {pesanGalat}
        </p>
      )}

      <Tombol
        type="button"
        varian="aksi"
        ikon={Send}
        sedangProses={buatKiriman.isPending}
        disabled={!bisaKirim}
        onClick={kirim}
        className="w-full"
      >
        Kirim
      </Tombol>

      <p className="text-center text-keterangan text-tanah/50">
        <PackagePlus aria-hidden className="mr-1 inline h-4 w-4" />
        Setelah terkirim, kamu langsung melihat muatanmu — harga atap terkunci, tidak pernah naik.
      </p>
    </div>
  );
}
