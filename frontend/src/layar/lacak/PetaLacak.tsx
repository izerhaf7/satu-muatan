/** Peta rute Lacak (§9.6) — Google Maps (K14).
 *
 *  Konsumsi instance peta + namespace lewat `usePeta()` dari BingkaiPeta.
 *  Marker posisi driver + tujuan penerima, polyline rute, jejak yang sudah
 *  dilalui, dan posisi terkini yang dianimasikan.
 *
 *  SUMBER RUTE (prioritas):
 *  1. `rutePolyline` backend bila itu rute JALAN sungguhan (Google Routes punya
 *     banyak titik); penentuannya heuristik: lebih dari 5 titik.
 *  2. Kalau backend hanya memberi garis lurus (fallback haversine, ≤ 5 titik)
 *     atau kosong, rute diminta ke Directions API di BROWSER — jadi peta tetap
 *     menampilkan jalan yang benar tanpa menunggu perbaikan snapshot backend.
 *  3. Keduanya gagal → garis lurus antar titik sebagai keadaan terakhir.
 *
 *  Rute tampil dime-mulai dari LOKASI DRIVER bila koordinat driver ada (kepala
 *  titik kumpul dibuang), dan lapisan peta dipecah statis/dinamis supaya
 *  polling GPS tidak membuat peta berkedip. */

import { useEffect, useRef, useState } from "react";

import BingkaiPeta, { usePeta } from "@/komponen/BingkaiPeta";
import { decodePolyline, interpolasiKoordinat, type Koordinat } from "@/utils/geometriRute";

interface TitikPeta {
  lat: number;
  lng: number;
  label: string;
}

interface PetaLacakProps {
  gudang: TitikPeta;
  tujuan: TitikPeta[];
  /** K14: perhentian penjemputan — ikut membentuk rute jalan yang diminta. */
  jemput?: TitikPeta[];
  posisiTerakhir?: TitikPeta | null;
  /** K13: titik-titik posisi yang sudah dilalui — digambar sebagai jejak
   *  berjalan di atas garis rute, supaya peta benar-benar bergerak. */
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

/** Isi peta — dipanggil usePeta() di DALAM <BingkaiPeta> (context tersedia). */
function IsiPetaLacak({
  gudang,
  tujuan,
  jemput = [],
  posisiTerakhir,
  jejak = [],
  rutePolyline,
}: PetaLacakProps) {
  const { peta, marker, idPeta, siap } = usePeta();

  // Objek peta + status rute jalan (pergi ke DirectionsService maksimal sekali
  // per asal, agar GPS yang berubah-ubah tidak memicu permintaan berulang).
  const rutePolylineRef = useRef<google.maps.Polyline | null>(null);
  const jejakPolylineRef = useRef<google.maps.Polyline | null>(null);
  const markerGudangRef = useRef<google.maps.marker.AdvancedMarkerElement | null>(null);
  const markerTujuanRefs = useRef<google.maps.marker.AdvancedMarkerElement[]>([]);
  const markerPosisiRef = useRef<google.maps.marker.AdvancedMarkerElement | null>(null);
  const frameRef = useRef<number | null>(null);
  const posisiRef = useRef<TitikPeta | null | undefined>(posisiTerakhir);
  posisiRef.current = posisiTerakhir;
  const asalRuteRef = useRef<"gudang" | "driver" | null>(null);
  const [ruteJalan, setRuteJalan] = useState<Koordinat[] | null>(null);

  // Data turunan.
  const ruteDecoded = decodePolyline(rutePolyline);
  // Rute backend dianggap "jalan sungguhan" bila punya banyak titik. Fallback
  // haversine hanya menghasilkan segaris lurus (≤ 5 titik) — itu yang membuat
  // peta tampak seperti garis lurus antar titik.
  const ruteBackend: Koordinat[] = ruteDecoded && ruteDecoded.length > 5 ? ruteDecoded : [];
  const perhentian: TitikPeta[] = [...jemput, ...tujuan];
  const ruteDasar: Koordinat[] =
    ruteBackend.length >= 2
      ? ruteBackend
      : [{ lat: gudang.lat, lng: gudang.lng }, ...perhentian.map((t) => ({ lat: t.lat, lng: t.lng }))];

  /** Rute yang ditampilkan: jarum utamanya rute jalan (backend/Browser), lalu
   *  kepala digeser ke lokasi driver bila koordinat driver ada. */
  const ruteUtama = ruteJalan ?? ruteDasar;
  const ruteTampil = (posisiAwal: TitikPeta | null | undefined): Koordinat[] => {
    if (posisiAwal) {
      const sisa = ruteUtama.slice(1);
      return sisa.length > 0 ? [{ lat: posisiAwal.lat, lng: posisiAwal.lng }, ...sisa] : ruteUtama;
    }
    return ruteUtama;
  };

  // -------------------------------------------------------------------------
  // Rute JALAN dari browser (Directions API) bila backend cuma garis lurus.
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!siap || !peta) return;
    if (typeof google === "undefined" || !google.maps || !google.maps.DirectionsService) return;
    if (perhentian.length === 0) return;

    const asal = posisiRef.current ? "driver" : "gudang";
    // Rute backend sudah jalan sungguhan — tidak perlu meminta lagi.
    if (ruteBackend.length > 5) {
      asalRuteRef.current = asal;
      return;
    }
    if (asalRuteRef.current === asal) return;
    asalRuteRef.current = asal;

    const asalTitik = posisiRef.current ?? gudang;
    const tujuanAkhir = perhentian[perhentian.length - 1];
    const waypoints = perhentian.slice(0, -1).map((t) => ({
      location: { lat: t.lat, lng: t.lng },
      stopover: true,
    }));

    const directions = new google.maps.DirectionsService();
    directions.route(
      {
        origin: { lat: asalTitik.lat, lng: asalTitik.lng },
        destination: { lat: tujuanAkhir.lat, lng: tujuanAkhir.lng },
        waypoints,
        travelMode: "DRIVING" as google.maps.TravelMode,
        optimizeWaypoints: false,
      },
      (respons, status) => {
        if (status !== google.maps.DirectionsStatus.OK) return;
        const jalur = respons?.routes?.[0]?.overview_path;
        if (!jalur || jalur.length < 2) return;
        const decoded: Koordinat[] = jalur.map((t) => koordinatDariPosisi(t));
        setRuteJalan(decoded);
      },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [siap, peta, ruteBackend, gudang, perhentian]);

  // -------------------------------------------------------------------------
  // Lapisan STATIS — redraw hanya saat rute/objek berubah. fitBounds di sini.
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!siap || !peta || !marker) return;

    const lamaRute = rutePolylineRef.current;
    lamaRute?.setMap(null);
    if (markerGudangRef.current) markerGudangRef.current.map = null;
    markerGudangRef.current = null;
    markerTujuanRefs.current.forEach((m) => {
      m.map = null;
    });
    markerTujuanRefs.current = [];

    // 1. Rute — polyline jalan sungguhan (backend Google atau Directions browser).
    const jalur = ruteTampil(posisiRef.current);
    if (jalur.length >= 2) {
      const sudahRuteJalan = (ruteJalan?.length ?? 0) >= 2 || ruteBackend.length > 5;
      const polyline = new google.maps.Polyline({
        path: jalur.map((t) => ({ lat: t.lat, lng: t.lng })),
        strokeColor: "#16A34A",
        strokeWeight: sudahRuteJalan ? 4 : 2,
        strokeOpacity: sudahRuteJalan ? 0.85 : 0.45,
        map: peta,
      });
      rutePolylineRef.current = polyline;
    }

    // 2. Marker gudang (titik kumpul) — disembunyikan saat rute berawal dari
    //    lokasi driver (kepala rute sudah berpindah ke posisi truk).
    markerGudangRef.current = new marker.AdvancedMarkerElement({
      map: posisiRef.current ? null : peta,
      position: { lat: gudang.lat, lng: gudang.lng },
      content: buatDivBundar("var(--tanah)", "G"),
      title: gudang.label,
    });

    // 3. Marker tujuan — lingkaran bernomor 1, 2, 3…
    perhentian.forEach((t, idx) => {
      const markerPerhentian = new marker.AdvancedMarkerElement({
        map: peta,
        position: { lat: t.lat, lng: t.lng },
        content: buatDivBundar("var(--daun)", String(idx + 1)),
        title: t.label,
      });
      markerTujuanRefs.current.push(markerPerhentian);
    });

    // 4. fitBounds — sekali per perubahan rute (bukan per polling GPS).
    const ukuran = peta.getDiv();
    if (ukuran && ukuran.clientWidth > 0 && ukuran.clientHeight > 0) {
      const bounds = new google.maps.LatLngBounds();
      jalur.forEach((t) => bounds.extend({ lat: t.lat, lng: t.lng }));
      if (posisiRef.current) bounds.extend({ lat: posisiRef.current.lat, lng: posisiRef.current.lng });
      if (!bounds.isEmpty()) {
        peta.fitBounds(bounds, 24);
      }
    }

    return () => {
      rutePolylineRef.current?.setMap(null);
      rutePolylineRef.current = null;
      if (markerGudangRef.current) markerGudangRef.current.map = null;
      markerGudangRef.current = null;
      markerTujuanRefs.current.forEach((m) => {
        m.map = null;
      });
      markerTujuanRefs.current = [];
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [siap, peta, marker, idPeta, rutePolyline, ruteJalan, gudang, perhentian]);

  // -------------------------------------------------------------------------
  // Kepala rute — geser in-place ke posisi driver + suai visibilitas marker G.
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!siap || !peta) return;
    const jalur = ruteTampil(posisiRef.current);
    if (rutePolylineRef.current) {
      rutePolylineRef.current.setPath(jalur.map((t) => ({ lat: t.lat, lng: t.lng })));
    }
    if (markerGudangRef.current) {
      markerGudangRef.current.map = posisiRef.current ? null : peta;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [siap, peta, posisiTerakhir, ruteJalan, rutePolyline, gudang, perhentian]);

  // -------------------------------------------------------------------------
  // Lapisan DINAMIS — jejak & marker posisi, diperbarui in-place tanpa redraw.
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!siap || !peta) return;

    if (jejak.length > 1) {
      if (!jejakPolylineRef.current) {
        jejakPolylineRef.current = new google.maps.Polyline({
          path: jejak.map((j) => ({ lat: j.lat, lng: j.lng })),
          strokeColor: "var(--daun)",
          strokeWeight: 4,
          map: peta,
        });
      } else {
        jejakPolylineRef.current.setPath(jejak.map((j) => ({ lat: j.lat, lng: j.lng })));
      }
    } else {
      jejakPolylineRef.current?.setMap(null);
      jejakPolylineRef.current = null;
    }

    return () => {
      jejakPolylineRef.current?.setMap(null);
      jejakPolylineRef.current = null;
    };
  }, [siap, peta, jejak]);

  // Marker posisi — dibuat sekali, posisinya diupdate in-place + dianimasikan.
  useEffect(() => {
    if (!peta || !marker) return;

    if (posisiTerakhir) {
      if (!markerPosisiRef.current) {
        markerPosisiRef.current = new marker.AdvancedMarkerElement({
          map: peta,
          position: { lat: posisiTerakhir.lat, lng: posisiTerakhir.lng },
          content: buatDivBundar("var(--tanah-liat)", "•"),
          title: posisiTerakhir.label,
        });
      } else {
        markerPosisiRef.current.map = peta;
      }
    } else if (markerPosisiRef.current) {
      markerPosisiRef.current.map = null;
    }

    return () => {
      if (markerPosisiRef.current) markerPosisiRef.current.map = null;
      markerPosisiRef.current = null;
    };
  }, [siap, peta, marker, posisiTerakhir]);

  // Animasi pergerakan marker posisi — interpolasi halus 2800ms.
  useEffect(() => {
    const markerPosisi = markerPosisiRef.current;
    if (!markerPosisi || !posisiTerakhir) return;

    const posisiSekarang = markerPosisi.position;
    const awal: Koordinat = posisiSekarang
      ? koordinatDariPosisi(posisiSekarang)
      : { lat: posisiTerakhir.lat, lng: posisiTerakhir.lng };
    const akhir: Koordinat = { lat: posisiTerakhir.lat, lng: posisiTerakhir.lng };

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [posisiTerakhir]);

  // Bersihkan seluruh lapisan saat unmount.
  useEffect(() => {
    const bersihkan = () => {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
        frameRef.current = null;
      }
      rutePolylineRef.current?.setMap(null);
      rutePolylineRef.current = null;
      jejakPolylineRef.current?.setMap(null);
      jejakPolylineRef.current = null;
      if (markerGudangRef.current) markerGudangRef.current.map = null;
      markerGudangRef.current = null;
      markerTujuanRefs.current.forEach((m) => {
        m.map = null;
      });
      markerTujuanRefs.current = [];
      if (markerPosisiRef.current) markerPosisiRef.current.map = null;
      markerPosisiRef.current = null;
    };
    return bersihkan;
  }, []);

  return (
    <div className="pointer-events-none" aria-hidden />
  );
}

/** Peta rute Lacak — wrapper yang menyediakan <BingkaiPeta> (Google Maps)
 *  supaya `usePeta()` di `IsiPetaLacak` selalu punya context. */
export default function PetaLacak({
  gudang,
  tujuan,
  jemput = [],
  posisiTerakhir,
  jejak = [],
  rutePolyline,
  className = "",
}: PetaLacakProps) {
  return (
    <BingkaiPeta className={className}>
      <IsiPetaLacak
        gudang={gudang}
        tujuan={tujuan}
        jemput={jemput}
        posisiTerakhir={posisiTerakhir}
        jejak={jejak}
        rutePolyline={rutePolyline}
      />
    </BingkaiPeta>
  );
}