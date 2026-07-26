/** Peta rute (react-router) — layar dibangun agent frontend-layar (spec §9). */

import { Navigate, Route, Routes } from "react-router-dom";

import Beranda from "./layar/Beranda";
import BuatSlot from "./layar/BuatSlot";
import DetailSlot from "./layar/DetailSlot";
import Masuk from "./layar/Masuk";
import Permintaan from "./layar/Permintaan";
import Riwayat from "./layar/Riwayat";
import { useAuthStore } from "./stores/authStore";

export default function App() {
  const token = useAuthStore((s) => s.token);
  const telahHidrasi = useAuthStore((s) => s.telahHidrasi);

  // Tunggu localStorage selesai dibaca dulu — cegah kedipan redirect ke /masuk saat refresh.
  if (!telahHidrasi) {
    return <div className="min-h-screen bg-kertas" />;
  }

  return (
    <Routes>
      <Route path="/masuk" element={token ? <Navigate to="/" replace /> : <Masuk />} />
      <Route path="/" element={token ? <Beranda /> : <Navigate to="/masuk" replace />} />
      <Route path="/slot/baru" element={token ? <BuatSlot /> : <Navigate to="/masuk" replace />} />
      <Route path="/slot/:id" element={token ? <DetailSlot /> : <Navigate to="/masuk" replace />} />
      <Route path="/riwayat" element={token ? <Riwayat /> : <Navigate to="/masuk" replace />} />
      <Route path="/permintaan" element={token ? <Permintaan /> : <Navigate to="/masuk" replace />} />
      <Route path="*" element={<Navigate to={token ? "/" : "/masuk"} replace />} />
    </Routes>
  );
}
