/** Pemilih titik di peta + tombol "Gunakan lokasi saya" (K14).
 *
 *  Menggantikan PetaPilihTujuan yang hanya bisa menaruh pin tujuan. Sekarang
 *  komponen yang sama dipakai untuk titik PENJEMPUTAN dan titik TUJUAN, dan
 *  setiap kali pin berpindah, alamatnya dibaca lewat `/api/geokode/balik` —
 *  pengguna melihat nama daerah, bukan angka lintang-bujur telanjang.
 *
 *  Di-lazy-load oleh KirimPanen supaya pustaka peta tidak ikut chunk awal.
 *
 *  Peta memakai Google Maps (K14) lewat <BingkaiPeta> — instance + namespace
 *  diambil dari `usePeta()`. Pin memakai AdvancedMarkerElement (butuh Map ID
 *  vektor), draggable lewat `gmpDraggable`, dan klik peta menaruh pin pending. */

import { useEffect, useRef } from "react";
import { AlertTriangle, Check, LocateFixed, X } from "lucide-react";

import BingkaiPeta, { usePeta } from "@/komponen/BingkaiPeta";
import Tombol from "@/komponen/Tombol";

import {
  bolehTerapkanHasilGps,
  opsiGpsSegar,
  pilihTitikGpsAktif,
  type SumberTitik,
  type TitikPending,
} from "./titikPending";

export interface Titik {
  lat: number;
  lng: number;
  akurasi_meter?: number;
  sumber?: SumberTitik;
  alamat?: string;
}

const AMBANG_AKURASI_GPS_RENDAH_METER = 100;

/** Bentuk event dragend AdvancedMarkerElement — punya `latLng` LatLng. */
type PeristiwaGeser = { latLng?: { lat: () => number; lng: () => number } };

/** Konten pin sebagai div HTML — warna & ukuran dari palet desain. */
function buatKontenPin(ukuran: number, warna: string): HTMLElement {
  const el = document.createElement("div");
  el.style.display = "flex";
  el.style.alignItems = "center";
  el.style.justifyContent = "center";
  el.style.width = `${ukuran}px`;
  el.style.height = `${ukuran}px`;
  el.style.borderRadius = "9999px";
  el.style.background = warna;
  el.style.border = "3px solid var(--kertas)";
  el.style.boxShadow = "0 1px 3px rgba(0,0,0,.3)";
  return el;
}

interface PetaPilihTitikProps {
  titik: Titik | null;
  pending: TitikPending | null;
  pusatAwal: Titik;
  onPending: (titik: Titik, sumber: SumberTitik) => void;
  onConfirm: () => void;
  onCancel: () => void;
  /** Sembunyikan tombol GPS di peta tujuan — lokasi perangkat bukan tujuannya. */
  tampilkanGps?: boolean;
}

export default function PetaPilihTitik({
  titik,
  pending,
  pusatAwal,
  onPending,
  onConfirm,
  onCancel,
  tampilkanGps = false,
}: PetaPilihTitikProps) {
  const { peta, marker: markerNs } = usePeta();
  const generasiPilihan = useRef(0);
  const titikPending = pending?.titik ?? null;
  const titikFokus = titikPending ?? titik;

  // onPending bisa berganti identitas — simpan di ref supaya listener marker
  // (yang dibuat sekali) selalu memanggil versi terbaru.
  const onPendingRef = useRef(onPending);
  useEffect(() => {
    onPendingRef.current = onPending;
  }, [onPending]);

  useEffect(() => {
    if (pending) generasiPilihan.current += 1;
  }, [pending?.titik.lat, pending?.titik.lng, pending?.sumber]);

  // Posisi awal — sekali saat peta siap (StrictMode aman lewat guard ref).
  const sudahPosisiAwal = useRef(false);
  useEffect(() => {
    if (!peta || sudahPosisiAwal.current) return;
    sudahPosisiAwal.current = true;
    const fokus = titikFokus ?? pusatAwal;
    peta.setCenter({ lat: fokus.lat, lng: fokus.lng });
    peta.setZoom(titik ? 13 : 10);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [peta]);

  // Ikuti perubahan titik dari luar (mis. autocomplete daerah).
  useEffect(() => {
    if (!peta || !titikFokus) return;
    peta.panTo({ lat: titikFokus.lat, lng: titikFokus.lng });
    peta.setZoom(Math.max(peta.getZoom() ?? 0, 12));
  }, [peta, titikFokus?.lat, titikFokus?.lng]);

  // Klik peta → ajukan titik pending.
  useEffect(() => {
    if (!peta) return;
    const listener = peta.addListener("click", (e: google.maps.MapMouseEvent) => {
      if (!e.latLng) return;
      generasiPilihan.current += 1;
      onPendingRef.current({ lat: e.latLng.lat(), lng: e.latLng.lng() }, "PETA");
    });
    return () => listener.remove();
  }, [peta]);

  // Pin terkonfirmasi + pin pending — draggable, dragend → GESER.
  const markerTerkonfirmasi = useRef<google.maps.marker.AdvancedMarkerElement | null>(null);
  const markerPending = useRef<google.maps.marker.AdvancedMarkerElement | null>(null);

  useEffect(() => {
    if (!peta || !markerNs) return;
    const { AdvancedMarkerElement } = markerNs;

    const pasangGeser = (marker: google.maps.marker.AdvancedMarkerElement) => {
      marker.addListener("dragend", (e: PeristiwaGeser) => {
        const pos = e.latLng;
        if (!pos) return;
        generasiPilihan.current += 1;
        onPendingRef.current({ lat: pos.lat(), lng: pos.lng() }, "GESER");
      });
    };

    if (titik) {
      if (!markerTerkonfirmasi.current) {
        markerTerkonfirmasi.current = new AdvancedMarkerElement({
          map: peta,
          gmpDraggable: true,
          content: buatKontenPin(22, "var(--tanah)"),
        });
        pasangGeser(markerTerkonfirmasi.current);
      }
      markerTerkonfirmasi.current.position = { lat: titik.lat, lng: titik.lng };
    } else if (markerTerkonfirmasi.current) {
      markerTerkonfirmasi.current.map = null;
      markerTerkonfirmasi.current = null;
    }

    if (titikPending) {
      if (!markerPending.current) {
        markerPending.current = new AdvancedMarkerElement({
          map: peta,
          gmpDraggable: true,
          content: buatKontenPin(28, "var(--daun)"),
        });
        pasangGeser(markerPending.current);
      }
      markerPending.current.position = { lat: titikPending.lat, lng: titikPending.lng };
    } else if (markerPending.current) {
      markerPending.current.map = null;
      markerPending.current = null;
    }
  }, [peta, markerNs, titik, titikPending]);

  // Bersihkan marker saat unmount.
  useEffect(() => {
    return () => {
      if (markerTerkonfirmasi.current) markerTerkonfirmasi.current.map = null;
      if (markerPending.current) markerPending.current.map = null;
      markerTerkonfirmasi.current = null;
      markerPending.current = null;
    };
  }, []);

  function pakaiLokasiSaya() {
    if (!navigator.geolocation) return;
    const generasiPermintaan = ++generasiPilihan.current;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        if (!bolehTerapkanHasilGps(generasiPermintaan, generasiPilihan.current)) return;
        onPending(
          { lat: pos.coords.latitude, lng: pos.coords.longitude, akurasi_meter: pos.coords.accuracy },
          "GPS",
        );
      },
      // Izin ditolak / GPS mati bukan galat yang perlu diributkan — pengguna
      // tetap bisa menaruh pin sendiri, yang memang cara utamanya.
      () => undefined,
      opsiGpsSegar(),
    );
  }

  const titikGps = pilihTitikGpsAktif(pending, titik);
  const akurasiGps = titikGps?.akurasi_meter;

  function konfirmasi() {
    generasiPilihan.current += 1;
    onConfirm();
  }

  function batalkan() {
    generasiPilihan.current += 1;
    onCancel();
  }

  const keteranganPending: Record<SumberTitik, string> = {
    PETA: "Titik dipilih dari peta.",
    GPS: "Titik ditemukan dari lokasi perangkat.",
    GESER: "Pin digeser ke titik baru.",
    WILAYAH: "Titik mengikuti wilayah yang dipilih.",
    ALAMAT: "Titik mengikuti alamat yang dipilih.",
  };
  const labelSumber: Record<SumberTitik, string> = {
    PETA: "pilihan peta",
    GPS: "GPS perangkat",
    GESER: "pin yang digeser",
    WILAYAH: "wilayah terpilih",
    ALAMAT: "alamat terpilih",
  };

  return (
    <div className="flex flex-col gap-2">
      <BingkaiPeta tinggi={240}>
        {/* Peta dibuat oleh BingkaiPeta; interaksi (klik, pin) dipasang lewat
            usePeta() di efek. Lapisan anak sengaja kosong supaya peta tetap
            bisa digeser (overlay anak ber-pointer-events-none). */}
        <></>
      </BingkaiPeta>

      {!pending && titik?.sumber && (
        <p className="text-keterangan text-tanah/55">Sumber titik: {labelSumber[titik.sumber]}.</p>
      )}

      {akurasiGps !== undefined && (
        <div
          role={akurasiGps > AMBANG_AKURASI_GPS_RENDAH_METER ? "alert" : "status"}
          className={`flex items-start gap-2 rounded-lg px-3 py-2 text-keterangan ${
            akurasiGps > AMBANG_AKURASI_GPS_RENDAH_METER
              ? "bg-tanah-liat/10 font-medium text-tanah-liat"
              : "bg-daun/10 text-daun"
          }`}
        >
          {akurasiGps > AMBANG_AKURASI_GPS_RENDAH_METER && (
            <AlertTriangle aria-hidden className="mt-0.5 h-4 w-4 shrink-0" />
          )}
          <p>
            Akurasi GPS ±{Math.round(akurasiGps)} m
            {akurasiGps > AMBANG_AKURASI_GPS_RENDAH_METER
              ? ". Akurasi rendah; periksa pin sebelum konfirmasi."
              : ""}
          </p>
        </div>
      )}

      {pending && (
        <div className="kartu-datar scroll-mb-28 flex flex-col gap-2 p-3" role="status" aria-live="polite">
          <p className="text-keterangan text-tanah/70">
            {keteranganPending[pending.sumber]} Konfirmasi agar alamat dan perhitungan memakai titik ini.
          </p>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <Tombol type="button" varian="aksi" ikon={Check} onClick={konfirmasi} className="w-full scroll-mb-28">
              Konfirmasi titik ini
            </Tombol>
            <Tombol type="button" varian="halus" ikon={X} onClick={batalkan} className="w-full scroll-mb-28">
              Batalkan perubahan
            </Tombol>
          </div>
        </div>
      )}

      {tampilkanGps && (
        <button
          type="button"
          onClick={pakaiLokasiSaya}
          className="inline-flex min-h-sentuh items-center justify-center gap-2 rounded-lg border-2 border-kabut px-4 text-base font-semibold text-tanah/70 transition-colors duration-cepat hover:border-daun hover:text-daun"
        >
          <LocateFixed aria-hidden className="h-4 w-4" />
          Gunakan lokasi saya
        </button>
      )}
    </div>
  );
}
