/** Peta rute Lacak (§9.6) — Leaflet + OpenStreetMap, BUKAN Google Maps (spec §3.1, §9.6:
 *  tidak butuh API key). Marker titik kumpul + tujuan penerima, garis rute, dan posisi
 *  terakhir kalau ada jejak. Tanpa ikon default Leaflet (path asetnya patah di bundler Vite) —
 *  dipakai divIcon sederhana dari palet desain, warna lewat custom property (temuan audit:
 *  hex hardcode + box-shadow tebal dihapus). */

import "leaflet/dist/leaflet.css";

import { DivIcon, type LatLngBoundsExpression } from "leaflet";
import { MapContainer, Marker, Polyline, Popup, TileLayer } from "react-leaflet";

import BingkaiPeta from "@/komponen/BingkaiPeta";

interface TitikPeta {
  lat: number;
  lng: number;
  label: string;
}

interface PetaLacakProps {
  gudang: TitikPeta;
  tujuan: TitikPeta[];
  posisiTerakhir?: TitikPeta | null;
  /** K13: titik-titik posisi yang sudah dilalui — digambar sebagai jejak
   *  berjalan di atas garis rute rencana, supaya peta benar-benar bergerak. */
  jejak?: { lat: number; lng: number }[];
  className?: string;
}

function ikonBundar(warna: string, isi: string): DivIcon {
  return new DivIcon({
    html: `<span style="display:flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:9999px;background:${warna};color:var(--kertas);font-family:'Plus Jakarta Sans Variable',system-ui,sans-serif;font-size:12px;font-weight:700;border:2px solid var(--kertas);">${isi}</span>`,
    className: "",
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
}

const IKON_GUDANG = ikonBundar("var(--tanah)", "G");
const IKON_POSISI = ikonBundar("var(--tanah-liat)", "•");

export default function PetaLacak({ gudang, tujuan, posisiTerakhir, jejak = [], className = "" }: PetaLacakProps) {
  const titikGudang: [number, number] = [gudang.lat, gudang.lng];
  const titikTujuan: [number, number][] = tujuan.map((t) => [t.lat, t.lng]);
  const titikJejak: [number, number][] = jejak.map((j) => [j.lat, j.lng]);
  const semuaTitik: [number, number][] = [
    titikGudang,
    ...titikTujuan,
    ...(posisiTerakhir ? ([[posisiTerakhir.lat, posisiTerakhir.lng]] as [number, number][]) : []),
  ];
  const bounds: LatLngBoundsExpression = semuaTitik;

  return (
    <BingkaiPeta className={className}>
      <MapContainer bounds={bounds} boundsOptions={{ padding: [24, 24] }} style={{ height: "100%", width: "100%" }} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {/* Rute rencana — tipis & putus-putus, jadi latar bagi jejak sungguhan. */}
        <Polyline
          positions={[titikGudang, ...titikTujuan]}
          pathOptions={{ color: "var(--daun)", weight: 2, opacity: 0.45, dashArray: "6 6" }}
        />
        {/* Jejak yang benar-benar sudah dilalui (K13). */}
        {titikJejak.length > 1 && (
          <Polyline positions={titikJejak} pathOptions={{ color: "var(--daun)", weight: 4 }} />
        )}

        <Marker position={titikGudang} icon={IKON_GUDANG}>
          <Popup>{gudang.label}</Popup>
        </Marker>

        {tujuan.map((t, idx) => (
          <Marker key={`${t.lat}-${t.lng}-${idx}`} position={[t.lat, t.lng]} icon={ikonBundar("var(--daun)", String(idx + 1))}>
            <Popup>{t.label}</Popup>
          </Marker>
        ))}

        {posisiTerakhir && (
          <Marker position={[posisiTerakhir.lat, posisiTerakhir.lng]} icon={IKON_POSISI}>
            <Popup>{posisiTerakhir.label}</Popup>
          </Marker>
        )}
      </MapContainer>
    </BingkaiPeta>
  );
}
