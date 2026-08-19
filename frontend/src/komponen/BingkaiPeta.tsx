/** Bingkai peta Google Maps — pengganti Leaflet (K14).
 *
 *  MEMBUAT MAP ID (WAJIB untuk AdvancedMarkerElement):
 *  Google Maps Platform → Maps JavaScript API → Map IDs → Create Map ID
 *  (atau Google Cloud Console → Maps Platform → Map Management). Pilih tipe
 *  "Vector" — AdvancedMarkerElement hanya berjalan di peta vektor yang punya
 *  Map ID. Isi hasilnya ke `VITE_GOOGLE_MAPS_ID`.
 *
 *  KUNCI API: `VITE_GOOGLE_MAPS_KEY` adalah browser key yang WAJIB dibatasi
 *  referrer (HTTP referrer) di Google Cloud Console — JANGAN pernah memakai
 *  server key / `GOOGLE_MAPS_API_KEY` di sini.
 *
 *  KONTRAK ANAK (PetaLacak / PetaPilihTitik):
 *  - Konsumsi instance peta + namespace lewat `usePeta()`.
 *  - Peta dibuat di div ref; anak dirender sebagai lapisan overlay
 *    `pointer-events-none` — elemen interaktif di anak wajib menyalakan
 *    `pointer-events-auto` sendiri supaya peta tetap bisa digeser.
 *  - `AdvancedMarkerElement` butuh `mapId` (dari context) + namespace `marker`.
 *  - `PetaReady` = hasil loader singleton (namespace + Map ID, tanpa instance);
 *    `NilaiPeta` = nilai context (instance + namespace + status). */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { importLibrary, setOptions, type LibraryMap } from "@googlemaps/js-api-loader";
import { MapPinOff } from "lucide-react";

import Tombol from "./Tombol";

interface BingkaiPetaProps {
  children: ReactNode;
  /** Tinggi peta dalam piksel — 360px tetap jadi acuan (CLAUDE.md aturan #6). */
  tinggi?: number;
  className?: string;
}

/** Hasil pemuatan singleton — namespace + Map ID yang dibutuhkan anak. */
export interface PetaReady {
  /** Kelas Map dari library "maps" — dipakai untuk membuat instance. */
  Map: typeof google.maps.Map;
  /** Namespace marker — AdvancedMarkerElement, PinElement. */
  marker: LibraryMap["marker"];
  /** Namespace geometry — spherical (jarak), encoding (polyline). */
  geometry: LibraryMap["geometry"];
  /** Map ID dari VITE_GOOGLE_MAPS_ID — wajib untuk AdvancedMarkerElement. */
  idPeta: string | undefined;
}

/** Nilai context yang dikonsumsi anak lewat usePeta(). */
export interface NilaiPeta {
  /** Instance Map Google yang sudah jadi — null sebelum siap. */
  peta: google.maps.Map | null;
  /** Namespace marker — tersedia saat siap. */
  marker: LibraryMap["marker"] | null;
  /** Namespace geometry — tersedia saat siap. */
  geometry: LibraryMap["geometry"] | null;
  /** Map ID — wajib untuk AdvancedMarkerElement. */
  idPeta: string | undefined;
  siap: boolean;
  gagal: boolean;
  /** Panggil untuk memuat ulang setelah gagal (kunci kosong / error skrip). */
  muatUlang: () => void;
}

const PetaContext = createContext<NilaiPeta | null>(null);

/** Akses instance peta + namespace dari dalam <BingkaiPeta>. */
export function usePeta(): NilaiPeta {
  const nilai = useContext(PetaContext);
  if (!nilai) throw new Error("usePeta() harus dipakai di dalam <BingkaiPeta>.");
  return nilai;
}

// Singleton loader — hanya SATU tag <script> Google Maps yang pernah dimuat,
// berapa pun jumlah <BingkaiPeta> di layar.
let janjiSiap: Promise<PetaReady> | null = null;

function siapkanPeta(): Promise<PetaReady> {
  if (!janjiSiap) {
    janjiSiap = (async () => {
      const kunci = import.meta.env.VITE_GOOGLE_MAPS_KEY;
      if (!kunci) throw new Error("VITE_GOOGLE_MAPS_KEY belum diisi.");
      setOptions({ key: kunci, v: "weekly" });
      const [maps, marker, geometry] = await Promise.all([
        importLibrary("maps"),
        importLibrary("marker"),
        importLibrary("geometry"),
      ]);
      return {
        Map: maps.Map,
        marker,
        geometry,
        idPeta: import.meta.env.VITE_GOOGLE_MAPS_ID,
      };
    })();
    // Gagal → reset supaya muatUlang() bisa mencoba dari awal.
    janjiSiap.catch(() => {
      janjiSiap = null;
    });
  }
  return janjiSiap;
}

export default function BingkaiPeta({ children, tinggi = 280, className = "" }: BingkaiPetaProps) {
  const wadahRef = useRef<HTMLDivElement | null>(null);
  const petaRef = useRef<google.maps.Map | null>(null);
  const markerRef = useRef<LibraryMap["marker"] | null>(null);
  const geometryRef = useRef<LibraryMap["geometry"] | null>(null);
  const dibuatRef = useRef(false);
  const [siap, setSiap] = useState(false);
  const [gagal, setGagal] = useState(false);
  const [versi, setVersi] = useState(0);

  useEffect(() => {
    // StrictMode (dev) memasang efek dua kali — inisialisasi cukup sekali.
    if (dibuatRef.current) return;
    dibuatRef.current = true;

    if (!import.meta.env.VITE_GOOGLE_MAPS_KEY) {
      setGagal(true);
      return;
    }

    siapkanPeta()
      .then((siap) => {
        // Wadah hilang (unmount sungguhan) → jangan buat peta.
        if (!wadahRef.current) return;
        markerRef.current = siap.marker;
        geometryRef.current = siap.geometry;
        petaRef.current = new siap.Map(wadahRef.current, {
          mapId: siap.idPeta,
          // "cooperative": scroll halaman tetap jalan, zoom butuh Ctrl/gesture
          // dua jari — pengganti scrollWheelZoom=false Leaflet yang aman di
          // desktop maupun mobile.
          gestureHandling: "cooperative",
          // Viewport awal wilayah demo; anak langsung menimpanya lewat
          // fitBounds()/setCenter() dari data masing-masing.
          center: { lat: -6.9175, lng: 107.6191 },
          zoom: 12,
          // Kontrol bawaan yang berisik di layar 360px.
          streetViewControl: false,
          mapTypeControl: false,
          fullscreenControl: false,
        });
        setSiap(true);
      })
      .catch(() => setGagal(true));

    return () => {
      // Google Maps tidak butuh destroy eksplisit — cukup lepas referensi
      // supaya listener tidak bocor.
      petaRef.current = null;
    };
  }, [versi]);

  const muatUlang = useCallback(() => {
    dibuatRef.current = false;
    petaRef.current = null;
    setSiap(false);
    setGagal(false);
    setVersi((v) => v + 1);
  }, []);

  const nilai = useMemo<NilaiPeta>(
    () => ({
      peta: petaRef.current,
      marker: markerRef.current,
      geometry: geometryRef.current,
      idPeta: import.meta.env.VITE_GOOGLE_MAPS_ID,
      siap,
      gagal,
      muatUlang,
    }),
    [siap, gagal, muatUlang],
  );

  return (
    <div className={`kartu-tonjol relative overflow-hidden rounded-xl ${className}`} style={{ height: tinggi }}>
      {gagal ? (
        <div className="kartu-datar flex h-full w-full flex-col items-center justify-center gap-3 border-0 p-4">
          <MapPinOff aria-hidden className="h-6 w-6 text-tanah/40" />
          <p className="text-keterangan text-tanah/60">Peta tidak tersedia</p>
          <Tombol varian="sekunder" onClick={muatUlang} className="min-h-11 px-4 text-keterangan">
            Muat ulang
          </Tombol>
        </div>
      ) : (
        <PetaContext.Provider value={nilai}>
          <div ref={wadahRef} className="absolute inset-0 h-full w-full" />
          {/* Lapisan anak: pointer-events-none supaya peta tetap bisa digeser;
              elemen interaktif di anak wajib pointer-events-auto. */}
          <div className="pointer-events-none absolute inset-0 z-10">{children}</div>
        </PetaContext.Provider>
      )}
    </div>
  );
}