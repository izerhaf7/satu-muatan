/** Peta rute Lacak (§9.6) — Google Maps (K14).
 *
 *  Konsumsi instance peta + namespace lewat `usePeta()` dari BingkaiPeta.
 *  Marker titik kumpul + tujuan penerima, garis rute rencana (putus-putus),
 *  jejak yang sudah dilalui, dan posisi terakhir yang dianimasikan.
 *
 *  Catatan dashed polyline: `@types/google.maps` tidak mengekspos
 *  `strokePattern` (properti runtime Maps JS), jadi dipakai `icons` +
 *  `IconSequence` dengan `Symbol` path garis pendek — cara yang type-check. */

import { useEffect, useRef } from "react";

import BingkaiPeta, { usePeta } from "@/komponen/BingkaiPeta";
import { decodePolyline, interpolasiKoordinat, proyeksikanKeRute, type Koordinat } from "@/utils/geometriRute";

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
  rutePolyline?: string | null;
  className?: string;
}

/** Bangun div bundar 26px untuk AdvancedMarkerElement — warna lewat custom
 *  property palet desain, teks putih, border kertas. */
function buatDivBundar(warna: string, isi: string): HTMLDivElement {
  const div = document.createElement("div");
  div.style.display = "flex";
  div.style.alignItems = "center";
  div.style.justifyContent = "center";
  div.style.width = "26px";
  div.style.height = "26px";
  div.style.borderRadius = "9999px";
  div.style.background = warna;
  div.style.color = "var(--kertas)";
  div.style.fontFamily = "'Plus Jakarta Sans Variable', system-ui, sans-serif";
  div.style.fontSize = "12px";
  div.style.fontWeight = "700";
  div.style.border = "2px solid var(--kertas)";
  div.textContent = isi;
  return div;
}

/** Ambil {lat,lng} dari posisi AdvancedMarkerElement — bisa berupa LatLng
 *  (getter fungsi) atau LatLngLiteral (angka). */
function koordinatDariPosisi(posisi: google.maps.LatLng | google.maps.LatLngLiteral | google.maps.LatLngAltitude | google.maps.LatLngAltitudeLiteral): Koordinat {
  if (posisi instanceof google.maps.LatLng) {
    return { lat: posisi.lat(), lng: posisi.lng() };
  }
  return { lat: posisi.lat, lng: posisi.lng };
}

export default function PetaLacak({
  gudang,
  tujuan,
  posisiTerakhir,
  jejak = [],
  rutePolyline,
  className = "",
}: PetaLacakProps) {
  const { peta, marker, idPeta, siap } = usePeta();

  // Objek yang dibuat — dibersihkan saat unmount / prop berubah.
  const polylinesRef = useRef<google.maps.Polyline[]>([]);
  const markersRef = useRef<google.maps.marker.AdvancedMarkerElement[]>([]);
  const markerPosisiRef = useRef<google.maps.marker.AdvancedMarkerElement | null>(null);
  const frameRef = useRef<number | null>(null);

  // Data turunan.
  const ruteDecoded = decodePolyline(rutePolyline);
  const ruteRencana: Koordinat[] = ruteDecoded
    ? ruteDecoded
    : [{ lat: gudang.lat, lng: gudang.lng }, ...tujuan.map((t) => ({ lat: t.lat, lng: t.lng }))];
  const posisiTampil: TitikPeta | null | undefined =
    posisiTerakhir && ruteDecoded
      ? { ...proyeksikanKeRute(posisiTerakhir, ruteDecoded), label: posisiTerakhir.label }
      : posisiTerakhir;

  // Bersihkan semua objek peta yang pernah dibuat.
  const bersihkan = () => {
    if (frameRef.current !== null) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
    polylinesRef.current.forEach((p) => p.setMap(null));
    polylinesRef.current = [];
    markersRef.current.forEach((m) => {
      m.map = null;
    });
    markersRef.current = [];
    markerPosisiRef.current = null;
  };

  // Gambar ulang seluruh lapisan saat peta siap atau data berubah.
  useEffect(() => {
    if (!siap || !peta || !marker) return;

    bersihkan();

    // 1. Rute rencana — tipis & putus-putus, jadi latar bagi jejak sungguhan.
    const ruteRencanaPolyline = new google.maps.Polyline({
      path: ruteRencana.map((t) => ({ lat: t.lat, lng: t.lng })),
      strokeColor: "var(--daun)",
      strokeWeight: 2,
      strokeOpacity: 0.45,
      // Dashed: Symbol path garis pendek diulang tiap 12px (lihat catatan atas).
      icons: [
        {
          icon: { path: "M 0,-1 0,1", strokeOpacity: 1, scale: 4 },
          offset: "0",
          repeat: "12px",
        },
      ],
      map: peta,
    });
    polylinesRef.current.push(ruteRencanaPolyline);

    // 2. Jejak yang benar-benar sudah dilalui (K13) — solid & lebih tebal.
    if (jejak.length > 1) {
      const jejakPolyline = new google.maps.Polyline({
        path: jejak.map((j) => ({ lat: j.lat, lng: j.lng })),
        strokeColor: "var(--daun)",
        strokeWeight: 4,
        map: peta,
      });
      polylinesRef.current.push(jejakPolyline);
    }

    // 3. Marker gudang (titik kumpul).
    const markerGudang = new marker.AdvancedMarkerElement({
      map: peta,
      position: { lat: gudang.lat, lng: gudang.lng },
      content: buatDivBundar("var(--tanah)", "G"),
      title: gudang.label,
    });
    markersRef.current.push(markerGudang);

    // 4. Marker tujuan — lingkaran bernomor 1, 2, 3…
    tujuan.forEach((t, idx) => {
      const markerTujuan = new marker.AdvancedMarkerElement({
        map: peta,
        position: { lat: t.lat, lng: t.lng },
        content: buatDivBundar("var(--daun)", String(idx + 1)),
        title: t.label,
      });
      markersRef.current.push(markerTujuan);
    });

    // 5. Marker posisi — dianimasikan kalau berubah.
    if (posisiTampil) {
      const markerPosisi = new marker.AdvancedMarkerElement({
        map: peta,
        position: { lat: posisiTampil.lat, lng: posisiTampil.lng },
        content: buatDivBundar("var(--tanah-liat)", "•"),
        title: posisiTampil.label,
      });
      markerPosisiRef.current = markerPosisi;
      markersRef.current.push(markerPosisi);
    }

    // 6. fitBounds — hanya saat data hadir dan peta sudah punya ukuran.
    const ukuran = peta.getDiv();
    if (ukuran && ukuran.clientWidth > 0 && ukuran.clientHeight > 0) {
      const bounds = new google.maps.LatLngBounds();
      ruteRencana.forEach((t) => bounds.extend({ lat: t.lat, lng: t.lng }));
      if (posisiTampil) bounds.extend({ lat: posisiTampil.lat, lng: posisiTampil.lng });
      if (!bounds.isEmpty()) {
        peta.fitBounds(bounds, 24);
      }
    }

    return bersihkan;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [siap, peta, marker, idPeta, rutePolyline, posisiTerakhir, jejak, gudang, tujuan]);

  // Animasi posisi terakhir — mirror MarkerPosisi: interpolasi 2800ms.
  useEffect(() => {
    const markerPosisi = markerPosisiRef.current;
    if (!markerPosisi || !posisiTampil) return;

    const posisiSekarang = markerPosisi.position;
    const awal: Koordinat = posisiSekarang
      ? koordinatDariPosisi(posisiSekarang)
      : { lat: posisiTampil.lat, lng: posisiTampil.lng };
    const akhir: Koordinat = { lat: posisiTampil.lat, lng: posisiTampil.lng };

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      markerPosisi.position = akhir;
      return;
    }

    if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    const mulai = performance.now();
    const durasi = 2800;
    const animasikan = (sekarang: number) => {
      const progres = Math.min((sekarang - mulai) / durasi, 1);
      const titik = interpolasiKoordinat(awal, akhir, progres);
      markerPosisi.position = { lat: titik.lat, lng: titik.lng };
      if (progres < 1) frameRef.current = requestAnimationFrame(animasikan);
      else frameRef.current = null;
    };
    frameRef.current = requestAnimationFrame(animasikan);

    return () => {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
        frameRef.current = null;
      }
    };
  }, [posisiTampil]);

  return (
    <BingkaiPeta className={className}>
      {/* Anak dirender sebagai overlay pointer-events-none (lihat BingkaiPeta);
          tidak ada elemen interaktif di sini, jadi tidak perlu pointer-events-auto. */}
      <div className="pointer-events-none" aria-hidden />
    </BingkaiPeta>
  );
}
