/** Kompresi foto di client sebelum dikirim ke server (spec §3.1, §9.5, §9.7).
 *  Foto disimpan sebagai base64 di kolom TEXT (tanpa object storage) — batasi ke
 *  maksimum 800px di sisi terpanjang dan encode JPEG supaya ukuran payload wajar.
 *  Hasil berupa data URL utuh ("data:image/jpeg;base64,...") — siap dipakai langsung
 *  sebagai `src` <img> saat pratinjau maupun saat ditampilkan ulang dari server. */

const SISI_MAKS_PX = 800;
const KUALITAS_JPEG = 0.8;

/** Baca File gambar, resize proporsional ke maksimum 800px, kompres ke JPEG,
 *  kembalikan data URL base64. Menolak file yang bukan gambar. */
export function kompresiFoto(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith("image/")) {
      reject(new Error("Berkas yang dipilih bukan gambar."));
      return;
    }

    const gambar = new Image();
    const urlSumber = URL.createObjectURL(file);

    gambar.onload = () => {
      URL.revokeObjectURL(urlSumber);

      let { width, height } = gambar;
      if (width > SISI_MAKS_PX || height > SISI_MAKS_PX) {
        if (width >= height) {
          height = Math.round((height / width) * SISI_MAKS_PX);
          width = SISI_MAKS_PX;
        } else {
          width = Math.round((width / height) * SISI_MAKS_PX);
          height = SISI_MAKS_PX;
        }
      }

      const kanvas = document.createElement("canvas");
      kanvas.width = width;
      kanvas.height = height;
      const ctx = kanvas.getContext("2d");
      if (!ctx) {
        reject(new Error("Tidak bisa memproses gambar di perangkat ini."));
        return;
      }
      ctx.drawImage(gambar, 0, 0, width, height);
      resolve(kanvas.toDataURL("image/jpeg", KUALITAS_JPEG));
    };

    gambar.onerror = () => {
      URL.revokeObjectURL(urlSumber);
      reject(new Error("Gagal membaca berkas gambar."));
    };

    gambar.src = urlSumber;
  });
}
