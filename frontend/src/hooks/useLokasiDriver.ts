import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { api } from "@/api/client";

type StatusLokasi = "meminta" | "aktif" | "ditolak" | "tidak_didukung" | "galat";

interface PosisiDriver {
  lat: number;
  lng: number;
  akurasi_m: number;
}

export function useLokasiDriver(aktif: boolean) {
  const queryClient = useQueryClient();
  const posisiTerakhir = useRef<PosisiDriver | null>(null);
  const [status, setStatus] = useState<StatusLokasi>(aktif ? "meminta" : "tidak_didukung");

  useEffect(() => {
    if (!aktif) return;
    if (!navigator.geolocation) {
      setStatus("tidak_didukung");
      return;
    }

    let masihTerpasang = true;
    let sudahKirimAwal = false;
    const kirimPosisi = async (posisi: PosisiDriver) => {
      try {
        await api<{ lat: number; lng: number; diperbarui_pada: string }>("/api/pengguna/lokasi", {
          method: "POST",
          body: JSON.stringify({ lat: posisi.lat, lng: posisi.lng }),
        });
        if (masihTerpasang) {
          setStatus("aktif");
          void queryClient.invalidateQueries({ queryKey: ["slot", "tersedia"] });
        }
      } catch {
        if (masihTerpasang) setStatus("galat");
      }
    };

    const tanganiPosisi = (posisi: GeolocationPosition) => {
      const terbaru = {
        lat: posisi.coords.latitude,
        lng: posisi.coords.longitude,
        akurasi_m: posisi.coords.accuracy,
      };
      posisiTerakhir.current = terbaru;
      if (!sudahKirimAwal) {
        sudahKirimAwal = true;
        void kirimPosisi(terbaru);
      }
    };

    const tanganiGalat = (galat: GeolocationPositionError) => {
      if (!masihTerpasang) return;
      if (galat.code === galat.PERMISSION_DENIED) setStatus("ditolak");
      else setStatus("galat");
    };

    const watchId = navigator.geolocation.watchPosition(tanganiPosisi, tanganiGalat, {
      enableHighAccuracy: true,
      maximumAge: 5_000,
      timeout: 10_000,
    });
    const intervalId = window.setInterval(() => {
      if (posisiTerakhir.current) void kirimPosisi(posisiTerakhir.current);
    }, 30_000);

    return () => {
      masihTerpasang = false;
      navigator.geolocation.clearWatch(watchId);
      window.clearInterval(intervalId);
    };
  }, [aktif, queryClient]);

  return { status, posisi: posisiTerakhir.current };
}
