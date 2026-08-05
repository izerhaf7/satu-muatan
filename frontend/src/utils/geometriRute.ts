export interface Koordinat {
  lat: number;
  lng: number;
}

const SKALA_POLYLINE = 1e5;
export const BATAS_KARAKTER_POLYLINE = 100_000;
export const BATAS_TITIK_POLYLINE = 10_000;

function koordinatValid(titik: Koordinat): boolean {
  return (
    Number.isFinite(titik.lat) &&
    Number.isFinite(titik.lng) &&
    titik.lat >= -90 &&
    titik.lat <= 90 &&
    titik.lng >= -180 &&
    titik.lng <= 180
  );
}

function bacaNilai(encoded: string, indeksAwal: number): { nilai: number; indeks: number } | null {
  let hasil = 0;
  let geser = 0;
  let indeks = indeksAwal;

  while (indeks < encoded.length && geser <= 30) {
    const kode = encoded.charCodeAt(indeks) - 63;
    if (kode < 0 || kode > 63) return null;
    indeks += 1;
    hasil |= (kode & 0x1f) << geser;
    if (kode < 0x20) {
      return { nilai: hasil & 1 ? ~(hasil >> 1) : hasil >> 1, indeks };
    }
    geser += 5;
  }

  return null;
}

/** Decoder kecil untuk format encoded polyline Google dengan presisi 1e-5. */
export function decodePolyline(encoded: string | null | undefined): Koordinat[] | null {
  if (!encoded || encoded.length > BATAS_KARAKTER_POLYLINE) return null;

  const titik: Koordinat[] = [];
  let indeks = 0;
  let lat = 0;
  let lng = 0;

  while (indeks < encoded.length) {
    const deltaLat = bacaNilai(encoded, indeks);
    if (!deltaLat) return null;
    const deltaLng = bacaNilai(encoded, deltaLat.indeks);
    if (!deltaLng) return null;

    lat += deltaLat.nilai;
    lng += deltaLng.nilai;
    indeks = deltaLng.indeks;

    const hasil = { lat: lat / SKALA_POLYLINE, lng: lng / SKALA_POLYLINE };
    if (!koordinatValid(hasil)) return null;
    if (titik.length >= BATAS_TITIK_POLYLINE) return null;
    titik.push(hasil);
  }

  return titik.length >= 2 ? titik : null;
}

export function pilihRuteTampil(encoded: string | null | undefined, fallback: Koordinat[]): Koordinat[] {
  return decodePolyline(encoded) ?? fallback;
}

export function interpolasiKoordinat(awal: Koordinat, akhir: Koordinat, progres: number): Koordinat {
  return {
    lat: awal.lat + (akhir.lat - awal.lat) * progres,
    lng: awal.lng + (akhir.lng - awal.lng) * progres,
  };
}

/** Proyeksi lokal per segmen memakai bidang equirectangular; cukup akurat untuk
 *  memilih titik terdekat pada rute jalan dan tetap stabil terhadap bujur. */
export function proyeksikanKeRute(posisi: Koordinat, rute: Koordinat[]): Koordinat {
  if (!koordinatValid(posisi) || rute.length < 2 || rute.some((titik) => !koordinatValid(titik))) return posisi;

  const radian = Math.PI / 180;
  const lintangAcuan = posisi.lat * radian;
  const skalaLng = Math.cos(lintangAcuan);
  let terdekat = posisi;
  let jarakKuadratTerdekat = Number.POSITIVE_INFINITY;

  for (let indeks = 0; indeks < rute.length - 1; indeks += 1) {
    const awal = rute[indeks];
    const akhir = rute[indeks + 1];
    const ax = (awal.lng - posisi.lng) * skalaLng;
    const ay = awal.lat - posisi.lat;
    const bx = (akhir.lng - posisi.lng) * skalaLng;
    const by = akhir.lat - posisi.lat;
    const dx = bx - ax;
    const dy = by - ay;
    const panjangKuadrat = dx * dx + dy * dy;
    const fraksi = panjangKuadrat === 0 ? 0 : Math.max(0, Math.min(1, -(ax * dx + ay * dy) / panjangKuadrat));
    const x = ax + fraksi * dx;
    const y = ay + fraksi * dy;
    const jarakKuadrat = x * x + y * y;

    if (jarakKuadrat < jarakKuadratTerdekat) {
      jarakKuadratTerdekat = jarakKuadrat;
      terdekat = {
        lat: awal.lat + fraksi * (akhir.lat - awal.lat),
        lng: awal.lng + fraksi * (akhir.lng - awal.lng),
      };
    }
  }

  return terdekat;
}
