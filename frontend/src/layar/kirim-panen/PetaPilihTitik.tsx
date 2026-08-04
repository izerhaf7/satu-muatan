/** Pemilih titik di peta + tombol "Gunakan lokasi saya" (K14).
 *
 *  Menggantikan PetaPilihTujuan yang hanya bisa menaruh pin tujuan. Sekarang
 *  komponen yang sama dipakai untuk titik PENJEMPUTAN dan titik TUJUAN, dan
 *  setiap kali pin berpindah, alamatnya dibaca lewat `/api/geokode/balik` —
 *  pengguna melihat nama daerah, bukan angka lintang-bujur telanjang.
 *
 *  Di-lazy-load oleh KirimPanen supaya Leaflet tidak ikut chunk masuk. */

import "leaflet/dist/leaflet.css";

import { useEffect } from "react";
import { DivIcon } from "leaflet";
import { LocateFixed } from "lucide-react";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";

import BingkaiPeta from "@/komponen/BingkaiPeta";

export interface Titik {
  lat: number;
  lng: number;
}

const IKON_PIN = new DivIcon({
  html: `<span style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:9999px;background:var(--daun);color:var(--kertas);border:3px solid var(--kertas);box-shadow:0 1px 3px rgba(0,0,0,.3);"></span>`,
  className: "",
  iconSize: [28, 28],
  iconAnchor: [14, 14],
});

function PenangkapKlik({ onPilih }: { onPilih: (t: Titik) => void }) {
  useMapEvents({
    click(e) {
      onPilih({ lat: e.latlng.lat, lng: e.latlng.lng });
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
  pusatAwal: Titik;
  onPilih: (t: Titik) => void;
  /** Sembunyikan tombol GPS di peta tujuan — lokasi perangkat bukan tujuannya. */
  tampilkanGps?: boolean;
}

export default function PetaPilihTitik({
  titik,
  pusatAwal,
  onPilih,
  tampilkanGps = false,
}: PetaPilihTitikProps) {
  const pusat: [number, number] = titik ? [titik.lat, titik.lng] : [pusatAwal.lat, pusatAwal.lng];

  function pakaiLokasiSaya() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => onPilih({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      // Izin ditolak / GPS mati bukan galat yang perlu diributkan — pengguna
      // tetap bisa menaruh pin sendiri, yang memang cara utamanya.
      () => undefined,
      { enableHighAccuracy: true, timeout: 8000 },
    );
  }

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
          <PenangkapKlik onPilih={onPilih} />
          <IkutiTitik titik={titik} />
          {titik && <Marker position={[titik.lat, titik.lng]} icon={IKON_PIN} />}
        </MapContainer>
      </BingkaiPeta>

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
