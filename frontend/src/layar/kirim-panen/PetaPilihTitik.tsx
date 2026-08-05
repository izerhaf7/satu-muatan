/** Pemilih titik di peta + tombol "Gunakan lokasi saya" (K14).
 *
 *  Menggantikan PetaPilihTujuan yang hanya bisa menaruh pin tujuan. Sekarang
 *  komponen yang sama dipakai untuk titik PENJEMPUTAN dan titik TUJUAN, dan
 *  setiap kali pin berpindah, alamatnya dibaca lewat `/api/geokode/balik` —
 *  pengguna melihat nama daerah, bukan angka lintang-bujur telanjang.
 *
 *  Di-lazy-load oleh KirimPanen supaya Leaflet tidak ikut chunk masuk. */

import "leaflet/dist/leaflet.css";

import { useEffect, useMemo, useRef } from "react";
import { DivIcon, type LeafletEvent } from "leaflet";
import { AlertTriangle, Check, LocateFixed, X } from "lucide-react";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";

import BingkaiPeta from "@/komponen/BingkaiPeta";
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

const IKON_PIN = new DivIcon({
  html: `<span style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:9999px;background:var(--daun);color:var(--kertas);border:3px solid var(--kertas);box-shadow:0 1px 3px rgba(0,0,0,.3);"></span>`,
  className: "",
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

const IKON_TERKONFIRMASI = new DivIcon({
  html: `<span style="display:flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:9999px;background:var(--tanah);color:var(--kertas);border:3px solid var(--kertas);box-shadow:0 1px 3px rgba(0,0,0,.3);"></span>`,
  className: "",
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

function PenangkapKlik({ onPending }: { onPending: (t: Titik) => void }) {
  useMapEvents({
    click(e) {
      onPending({ lat: e.latlng.lat, lng: e.latlng.lng });
    },
  });
  return null;
}

/** Pindahkan peta saat titik berubah dari luar (mis. autocomplete daerah). */
function IkutiTitik({ titik }: { titik: Titik | null }) {
  const peta = useMap();
  useEffect(() => {
    if (titik) peta.setView([titik.lat, titik.lng], Math.max(peta.getZoom(), 12));
  }, [titik?.lat, titik?.lng]);
  return null;
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
  const generasiPilihan = useRef(0);
  const titikPending = pending?.titik ?? null;
  const titikFokus = titikPending ?? titik;
  useEffect(() => {
    if (pending) generasiPilihan.current += 1;
  }, [pending?.titik.lat, pending?.titik.lng, pending?.sumber]);
  const pusat: [number, number] = titikFokus
    ? [titikFokus.lat, titikFokus.lng]
    : [pusatAwal.lat, pusatAwal.lng];
  const eventHandlers = useMemo(
    () => ({
      dragend(e: LeafletEvent) {
        const posisi = e.target.getLatLng();
        generasiPilihan.current += 1;
        onPending({ lat: posisi.lat, lng: posisi.lng }, "GESER");
      },
    }),
    [onPending],
  );

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

  function ajukanDariPeta(titikBaru: Titik) {
    generasiPilihan.current += 1;
    onPending(titikBaru, "PETA");
  }

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
        <MapContainer
          center={pusat}
          zoom={titik ? 13 : 10}
          style={{ height: "100%", width: "100%" }}
          scrollWheelZoom={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <PenangkapKlik onPending={ajukanDariPeta} />
          <IkutiTitik titik={titikFokus} />
          {titik && (
            <Marker
              position={[titik.lat, titik.lng]}
              icon={pending ? IKON_TERKONFIRMASI : IKON_PIN}
              draggable
              eventHandlers={eventHandlers}
            />
          )}
          {titikPending && (
            <Marker
              position={[titikPending.lat, titikPending.lng]}
              icon={IKON_PIN}
              draggable
              eventHandlers={eventHandlers}
            />
          )}
        </MapContainer>
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
