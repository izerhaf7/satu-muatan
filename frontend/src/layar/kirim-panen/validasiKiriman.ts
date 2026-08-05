export interface KondisiKiriman {
  komoditasId: string;
  volumeKg: number;
  volumeMinimalKg: number | null;
  tanggal: string;
  ringkasanTujuan: string;
  adaTitikTujuan: boolean;
  tujuanPending: boolean;
  asalPending: boolean;
  alamatSedangDimuat: boolean;
  sedangMengirim: boolean;
}

export function daftarPenghambatKiriman(kondisi: KondisiKiriman): string[] {
  const penghambat: string[] = [];

  if (!kondisi.komoditasId) penghambat.push("Pilih komoditas yang akan dikirim.");

  if (!Number.isFinite(kondisi.volumeKg) || kondisi.volumeKg <= 0) {
    penghambat.push("Isi volume dengan angka lebih dari 0 kg.");
  } else if (kondisi.volumeMinimalKg !== null && kondisi.volumeKg < kondisi.volumeMinimalKg) {
    penghambat.push(`Tambah volume menjadi minimal ${kondisi.volumeMinimalKg} kg.`);
  }

  if (!kondisi.tanggal) penghambat.push("Pilih tanggal siap panen.");
  if (!kondisi.adaTitikTujuan) penghambat.push("Tandai titik tujuan di peta.");
  if (!kondisi.ringkasanTujuan.trim()) penghambat.push("Lengkapi alamat tujuan pengiriman.");
  if (kondisi.tujuanPending) penghambat.push("Konfirmasi atau batalkan titik tujuan yang baru.");
  if (kondisi.asalPending) penghambat.push("Konfirmasi atau batalkan titik penjemputan yang baru.");
  if (kondisi.alamatSedangDimuat) penghambat.push("Tunggu sampai alamat dari peta selesai dibaca.");
  if (kondisi.sedangMengirim) penghambat.push("Tunggu sampai pengiriman sebelumnya selesai diproses.");

  return penghambat;
}
