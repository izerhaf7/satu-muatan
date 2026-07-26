/** Hitung mundur ke cutoff_at (§9.2, §9.4). Dihitung terhadap offset waktu_server
 *  bila tersedia — supaya jam perangkat pengguna yang meleset tidak membuat
 *  hitungan salah (SlotDetailOut.waktu_server / SlotItemOut tidak menyediakannya
 *  di Beranda, jadi offset 0 pada kasus itu, cukup akurat untuk tampilan). */

import { useEffect, useState } from "react";

interface HitungMundurProps {
  cutoffAt: string;
  waktuServer?: string;
  className?: string;
}

function hitungSisaMs(cutoffAt: string, offsetMs: number): number {
  return new Date(cutoffAt).getTime() - (Date.now() + offsetMs);
}

export default function HitungMundur({ cutoffAt, waktuServer, className = "" }: HitungMundurProps) {
  const offsetMs = waktuServer ? new Date(waktuServer).getTime() - Date.now() : 0;
  const [sisaMs, setSisaMs] = useState(() => hitungSisaMs(cutoffAt, offsetMs));

  useEffect(() => {
    setSisaMs(hitungSisaMs(cutoffAt, offsetMs));
    const id = setInterval(() => {
      setSisaMs(hitungSisaMs(cutoffAt, offsetMs));
    }, 1000);
    return () => clearInterval(id);
  }, [cutoffAt, waktuServer]);

  if (sisaMs <= 0) {
    return <p className={`angka text-sm font-medium text-tanah-liat ${className}`}>Sudah ditutup</p>;
  }

  const totalDetik = Math.floor(sisaMs / 1000);
  const jam = Math.floor(totalDetik / 3600);
  const menit = Math.floor((totalDetik % 3600) / 60);
  const detik = totalDetik % 60;
  const dua = (n: number) => String(n).padStart(2, "0");

  return (
    <p className={`angka text-sm font-medium text-tanah ${className}`}>
      Tutup dalam {dua(jam)}:{dua(menit)}:{dua(detik)}
    </p>
  );
}
