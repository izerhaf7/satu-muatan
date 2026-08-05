export interface TitikKoordinat {
  lat: number;
  lng: number;
  akurasi_meter?: number;
  sumber?: SumberTitik;
  alamat?: string;
}

export type SumberTitik = "PETA" | "GPS" | "GESER" | "WILAYAH" | "ALAMAT";

export interface TitikPending {
  titik: TitikKoordinat;
  sumber: SumberTitik;
}

export interface StatusTitik {
  terkonfirmasi: TitikKoordinat | null;
  pending: TitikPending | null;
}

function sama(a: TitikKoordinat | null, b: TitikKoordinat | null): boolean {
  return a?.lat === b?.lat && a?.lng === b?.lng;
}

export function buatStatusTitik(terkonfirmasi: TitikKoordinat | null): StatusTitik {
  return { terkonfirmasi, pending: null };
}

export function simpanTitikPending(
  status: StatusTitik,
  titik: TitikKoordinat,
  sumber: SumberTitik,
): StatusTitik {
  return { ...status, pending: { titik, sumber } };
}

export function selaraskanTitikTerkonfirmasi(
  status: StatusTitik,
  terkonfirmasi: TitikKoordinat | null,
): StatusTitik {
  return sama(status.terkonfirmasi, terkonfirmasi) ? status : buatStatusTitik(terkonfirmasi);
}

export function konfirmasiTitikPending(
  status: StatusTitik,
): { status: StatusTitik; titik: TitikKoordinat } | null {
  if (!status.pending) return null;
  const titik = { ...status.pending.titik, sumber: status.pending.sumber };
  return {
    status: buatStatusTitik(titik),
    titik,
  };
}

export function opsiGpsSegar(): PositionOptions {
  return { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 };
}

export function bolehTerapkanHasilGps(generasiPermintaan: number, generasiAktif: number): boolean {
  return generasiPermintaan === generasiAktif;
}

export function pilihTitikGpsAktif(
  pending: TitikPending | null,
  terkonfirmasi: TitikKoordinat | null,
): TitikKoordinat | null {
  if (pending) return pending.sumber === "GPS" ? pending.titik : null;
  return terkonfirmasi?.sumber === "GPS" ? terkonfirmasi : null;
}

export function batalkanTitikPending(status: StatusTitik): StatusTitik {
  return { ...status, pending: null };
}

export function adaTitikPending(asal: StatusTitik, tujuan: StatusTitik): boolean {
  return asal.pending !== null || tujuan.pending !== null;
}
