/** Layar Kirim Panen (spec v2 §3.4, dirombak K14).
 *
 *  Alur petani: pilih komoditas & volume → tandai DARI MANA panennya dijemput →
 *  tandai KE MANA tujuannya → lihat atap & potensi harga → kirim. Sistem yang
 *  mencocokkan ke muatan; petani tidak pernah memilih slot.
 *
 *  Perubahan K14:
 *  - **Alamat penjemputan ada.** Sebelumnya asal kiriman tidak pernah ditanya:
 *    semua petani dianggap berangkat dari titik kumpul, jadi petugas tidak punya
 *    alamat untuk didatangi dan jarak muatan tidak menghitung leg jemput.
 *  - **Alamat terstruktur + autocomplete daerah**, mengikuti standar penulisan
 *    alamat ekspedisi — bukan lagi satu kotak teks bebas yang tidak terhubung
 *    ke pin di peta.
 *  - **Volume minimal diketahui klien** dari `/api/aturan-kiriman`, jadi petani
 *    tahu batasnya sebelum menekan tombol, bukan lewat galat 422 sesudahnya. */

import { Suspense, lazy, useEffect, useMemo, useState } from "react";
import { PackagePlus, Send, TrendingDown } from "lucide-react";
import { useNavigate } from "react-router-dom";

import FormAlamat, {
  ALAMAT_KOSONG,
  ringkasAlamat,
  terapkanGeokode,
  type NilaiAlamat,
} from "@/komponen/FormAlamat";
import HeaderLayar from "@/komponen/kerangka/HeaderLayar";
import InputTeks from "@/komponen/InputTeks";
import KartuGalat from "@/komponen/KartuGalat";
import { Skeleton, SkeletonKartu } from "@/komponen/Skeleton";
import Tombol from "@/komponen/Tombol";
import { ApiError } from "@/api/client";
import { useAturanKiriman } from "@/hooks/useAturanKiriman";
import { useGeokodeBalik } from "@/hooks/useAlamat";
import { useKomoditas } from "@/hooks/useKomoditas";
import { useTitikKumpulSaya } from "@/hooks/useTitikKumpul";
import { useBuatKiriman, usePratinjauKiriman, type ParamsPratinjau } from "@/hooks/useKiriman";
import { formatRupiah } from "@/utils/format";

import type { Titik } from "./kirim-panen/PetaPilihTitik";

// Leaflet berat — jangan sampai ikut chunk masuk aplikasi.
const PetaPilihTitik = lazy(() => import("./kirim-panen/PetaPilihTitik"));

function tanggalBesok(): string {
  const d = new Date();
  d.setDate(d.getDate() + 1);
  return d.toISOString().slice(0, 10);
}

export default function KirimPanen() {
  const navigate = useNavigate();
  const komoditas = useKomoditas();
  const titikKumpul = useTitikKumpulSaya();
  const aturan = useAturanKiriman();
  const buatKiriman = useBuatKiriman();

  const [komoditasId, setKomoditasId] = useState("");
  const [volume, setVolume] = useState("");
  const [tanggal, setTanggal] = useState(tanggalBesok());

  const [titikAsal, setTitikAsal] = useState<Titik | null>(null);
  const [alamatAsal, setAlamatAsal] = useState<NilaiAlamat>(ALAMAT_KOSONG);
  const [titikTujuan, setTitikTujuan] = useState<Titik | null>(null);
  const [alamatTujuan, setAlamatTujuan] = useState<NilaiAlamat>(ALAMAT_KOSONG);

  // Pin berpindah → alamat dibaca ulang. Hasilnya melengkapi isian yang masih
  // kosong dan TIDAK menimpa apa yang sudah diketik pengguna.
  const geokodeAsal = useGeokodeBalik(titikAsal);
  const geokodeTujuan = useGeokodeBalik(titikTujuan);

  useEffect(() => {
    if (geokodeAsal.data) setAlamatAsal((a) => terapkanGeokode(a, geokodeAsal.data));
  }, [geokodeAsal.data]);

  useEffect(() => {
    if (geokodeTujuan.data) setAlamatTujuan((a) => terapkanGeokode(a, geokodeTujuan.data));
  }, [geokodeTujuan.data]);

  const volumeMinimal = aturan.data?.volume_minimal_kg ?? null;
  const volumeAngka = Number(volume);
  const volumeKurang =
    volumeMinimal !== null && volume.trim().length > 0 && volumeAngka > 0 && volumeAngka < volumeMinimal;

  const paramsPratinjau: ParamsPratinjau | null = useMemo(() => {
    if (!titikTujuan || !volumeAngka || volumeAngka <= 0 || !tanggal) return null;
    return { volumeKg: volumeAngka, lat: titikTujuan.lat, lng: titikTujuan.lng, tanggal };
  }, [volumeAngka, tanggal, titikTujuan]);

  const pratinjau = usePratinjauKiriman(paramsPratinjau);

  const ringkasanTujuan = ringkasAlamat(alamatTujuan);
  const bisaKirim =
    Boolean(komoditasId) &&
    volumeAngka > 0 &&
    !volumeKurang &&
    Boolean(tanggal) &&
    titikTujuan !== null &&
    ringkasanTujuan.length > 0 &&
    !buatKiriman.isPending;

  async function kirim() {
    if (!bisaKirim || !titikTujuan) return;
    try {
      const hasil = await buatKiriman.mutateAsync({
        komoditas_id: komoditasId,
        volume_kg: volumeAngka,
        tanggal_siap: tanggal,
        lat_tujuan: titikTujuan.lat,
        lng_tujuan: titikTujuan.lng,
        alamat_tujuan: ringkasanTujuan,
        rincian_tujuan: { ...alamatTujuan, alamat: ringkasanTujuan },
        lat_asal: titikAsal?.lat ?? null,
        lng_asal: titikAsal?.lng ?? null,
        rincian_asal: titikAsal ? { ...alamatAsal, alamat: ringkasAlamat(alamatAsal) } : null,
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

  const pusatAwal: Titik = titikKumpul.data
    ? { lat: titikKumpul.data.lat, lng: titikKumpul.data.lng }
    : { lat: -6.95, lng: 107.65 };

  function keteranganGeokode(sedangMemuat: boolean, sumber: string | undefined): string {
    if (sedangMemuat) return "Membaca alamat dari titik di peta…";
    if (sumber === "GOOGLE") return "Alamat terbaca dari peta. Periksa dan lengkapi bila perlu.";
    if (sumber === "LOKAL")
      return "Daerah terdekat terisi otomatis. Lengkapi nama jalan & patokan supaya mudah ditemukan.";
    return "Ketuk peta untuk menandai titiknya.";
  }

  return (
    <div className="flex flex-col gap-6">
      <HeaderLayar judul="Kirim Panen" subjudul="Sistem yang mencocokkan muatan untukmu" kembaliKe="/beranda" />

      <section className="flex flex-col gap-3">
        <label htmlFor="komoditas" className="text-keterangan font-semibold text-tanah">
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

      <div className="flex flex-col gap-1.5">
        <div className="grid grid-cols-2 gap-3">
          <InputTeks
            label="Volume (kg)"
            id="volume"
            type="number"
            inputMode="numeric"
            min={volumeMinimal ?? 1}
            value={volume}
            onChange={(e) => setVolume(e.target.value)}
            className="angka text-lg font-semibold"
            aria-describedby="bantuan-volume"
            aria-invalid={volumeKurang || undefined}
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
        {volumeMinimal !== null &&
          (volumeKurang ? (
            <p id="bantuan-volume" role="alert" className="text-keterangan font-medium text-tanah-liat">
              Volume minimal satu kiriman {volumeMinimal} kg (kamu mengisi {volumeAngka} kg).
            </p>
          ) : (
            <p id="bantuan-volume" className="text-keterangan text-tanah/55">
              Minimal <span className="angka">{volumeMinimal}</span> kg per kiriman.
            </p>
          ))}
      </div>

      {/* ---- Penjemputan ---------------------------------------------- */}
      <div className="flex flex-col gap-3 rounded-xl border-2 border-kabut p-4">
        <Suspense fallback={<Skeleton className="h-[240px] w-full" />}>
          <PetaPilihTitik titik={titikAsal} pusatAwal={pusatAwal} onPilih={setTitikAsal} tampilkanGps />
        </Suspense>
        <FormAlamat
          judul="Dijemput dari"
          idPrefix="asal"
          nilai={alamatAsal}
          onUbah={setAlamatAsal}
          labelNama="Nama pengirim"
          labelTelepon="Telepon pengirim"
          onWilayahBerkoordinat={setTitikAsal}
          keterangan={keteranganGeokode(geokodeAsal.isLoading, geokodeAsal.data?.sumber)}
        />
        {!titikAsal && (
          <p className="text-keterangan text-tanah/55">
            Belum ditandai — kalau dikosongkan, panenmu dianggap sudah ada di titik kumpul.
          </p>
        )}
      </div>

      {/* ---- Tujuan ---------------------------------------------------- */}
      <div className="flex flex-col gap-3 rounded-xl border-2 border-kabut p-4">
        <Suspense fallback={<Skeleton className="h-[240px] w-full" />}>
          <PetaPilihTitik titik={titikTujuan} pusatAwal={pusatAwal} onPilih={setTitikTujuan} />
        </Suspense>
        <FormAlamat
          judul="Diantar ke"
          idPrefix="tujuan"
          nilai={alamatTujuan}
          onUbah={setAlamatTujuan}
          labelNama="Nama penerima"
          labelTelepon="Telepon penerima"
          onWilayahBerkoordinat={setTitikTujuan}
          keterangan={keteranganGeokode(geokodeTujuan.isLoading, geokodeTujuan.data?.sumber)}
        />
        {!titikTujuan && (
          <p role="alert" className="text-keterangan font-medium text-tanah-liat">
            Tandai dulu titik tujuannya di peta.
          </p>
        )}
      </div>

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
