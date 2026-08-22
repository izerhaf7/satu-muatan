/** Peta rute Lacak (§9.6) — Google Maps (K14).
 *
 *  Konsumsi instance peta + namespace lewat `usePeta()` dari BingkaiPeta.
 *  Marker posisi driver + tujuan penerima, polyline rute provider, jejak yang
 *  sudah dilalui, dan posisi terkini yang dianimasikan.
 *
 *  Dua prinsip anti-kedip:
 *  - Lapisan STATIS (rute, marker gudang/tujuan, fitBounds) di-redraw hanya
 *    saat rute/objek berubah — bukan setiap polling jejak.
 *  - Lapisan DINAMIS (jejak + marker posisi) diperbarui in-place (setPath /
 *    posisi marker), tanpa membongkar seluruh peta, sehingga polling GPS tidak
 *    membuat peta berkedip.
 *
 *  Rute tampil dime-mulai dari LOKASI DRIVER bila ada koordinat driver: kepala
 *  titik kumpul dibuang, jadi halaman tidak selalu tampil berawal dari titik
 *  kumpul (mis. Cikajang) padahal truk memuat di tempat lain. */

import { useEffect, useRef } from "react";

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

/** Isi peta — dipanggil usePeta() di DALAM <BingkaiPeta> (context tersedia). */
function IsiPetaLacak({
  gudang,
  tujuan,
  posisiTerakhir,
  jejak = [],
  rutePolyline,
}: PetaLacakProps) {
  const { peta, marker, idPeta, siap } = usePeta();

  // Objek peta — dibersihkan saat unmount.
  const rutePolylineRef = useRef<google.maps.Polyline | null>(null);
  const jejakPolylineRef = useRef<google.maps.Polyline | null>(null);
  const markerGudangRef = useRef<google.maps.marker.AdvancedMarkerElement | null>(null);
  const markerTujuanRefs = useRef<google.maps.marker.AdvancedMarkerElement[]>([]);
  const markerPosisiRef = useRef<google.maps.marker.AdvancedMarkerElement | null>(null);
  const frameRef = useRef<number | null>(null);
  // Posisi terbaru agar lapisan statis bisa membaca kepala rute saat di-redraw
  // (ref, bukan state — tidak memicu render).
  const posisiRef = useRef<TitikPeta | null | undefined>(posisiTerakhir);
  posisiRef.current = posisiTerakhir;

  // Data turunan.
  const ruteDecoded = decodePolyline(rutePolyline);
  const ruteDasar: Koordinat[] = ruteDecoded
    ? ruteDecoded
    : [{ lat: gudang.lat, lng: gudang.lng }, ...tujuan.map((t) => ({ lat: t.lat, lng: t.lng }))];

  /** Rute yang ditampilkan: dimulai dari lokasi driver bila ada. Kepala titik
   *  kumpul dibuang agar peta tidak selalu berawal dari titik kumpul. */
  const ruteTampil = (posisiAwal: TitikPeta | null | undefined): Koordinat[] => {
    if (posisiAwal) {
      const sisa = ruteDasar.slice(1);
      return sisa.length > 0 ? [{ lat: posisiAwal.lat, lng: posisiAwal.lng }, ...sisa] : ruteDasar;
    }
    return ruteDasar;
  };

  // Bersihkan seluruh lapisan (unmount / perubahan statis).
  const bersihkanSemua = () => {
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

    // 1. Rute provider — polyline jalan sungguhan dari Google Routes.
    const jalur = ruteTampil(posisiRef.current);
    if (jalur.length >= 2) {
      const polyline = new google.maps.Polyline({
        path: jalur.map((t) => ({ lat: t.lat, lng: t.lng })),
        strokeColor: "#16A34A",
        strokeWeight: ruteDecoded ? 4 : 2,
        strokeOpacity: ruteDecoded ? 0.85 : 0.45,
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
    tujuan.forEach((t, idx) => {
      const markerTujuan = new marker.AdvancedMarkerElement({
        map: peta,
        position: { lat: t.lat, lng: t.lng },
        content: buatDivBundar("var(--daun)", String(idx + 1)),
        title: t.label,
      });
      markerTujuanRefs.current.push(markerTujuan);
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
  }, [siap, peta, marker, idPeta, rutePolyline, gudang, tujuan]);

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
  }, [siap, peta, posisiTerakhir, rutePolyline, gudang, tujuan]);

  // -------------------------------------------------------------------------
  // Lapisan DINAMIS — jejak & marker posisi, diperbarui in-place tanpa redraw.
  // -------------------------------------------------------------------------
  useEffect(() => {
    if (!siap || !peta) return;

    // 2. Jejak yang benar-benar sudah dilalui (K13).
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

  useEffect(() => bersihkanSemua, []);

  return (
    <div className="pointer-events-none" aria-hidden />
  );
}

/** Peta rute Lacak — wrapper yang menyediakan <BingkaiPeta> (Google Maps)
 *  supaya `usePeta()` di `IsiPetaLacak` selalu punya context. */
export default function PetaLacak({
  gudang,
  tujuan,
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
        posisiTerakhir={posisiTerakhir}
        jejak={jejak}
        rutePolyline={rutePolyline}
      />
    </BingkaiPeta>
  );
}