/** Pembungkus tipis lib `qrcode` — dipakai layar Muat untuk menampilkan QR per lot (§9.5). */

import QRCode from "qrcode";

/** Render teks jadi QR code sebagai data URL PNG, siap dipakai langsung sebagai `src` <img>. */
export function buatQrDataUrl(teks: string): Promise<string> {
  return QRCode.toDataURL(teks, {
    margin: 1,
    width: 240,
    color: { dark: "#0F2D4A", light: "#F5F6F8" },
  });
}
