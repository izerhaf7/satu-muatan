import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import RingkasanResi from "./RingkasanResi";

function buatResi() {
  const lotId = crypto.randomUUID();
  return { lot_id: lotId, kode_qr: crypto.randomUUID() };
}

describe("RingkasanResi", () => {
  it("tidak merender ringkasan ketika daftar resi kosong", () => {
    expect(renderToStaticMarkup(<RingkasanResi resi={[]} />)).toBe("");
  });

  it("tidak menjatuhkan layar untuk payload lama tanpa field resi", () => {
    expect(renderToStaticMarkup(<RingkasanResi resi={undefined} />)).toBe("");
  });

  it("merender label Nomor resi dan satu kode", () => {
    const resi = buatResi();
    const html = renderToStaticMarkup(<RingkasanResi resi={[resi]} />);

    expect(html).toContain("Nomor resi");
    expect(html).toContain(resi.kode_qr);
  });

  it("merender semua kode untuk muatan bersama", () => {
    const resi = [buatResi(), buatResi()];
    const html = renderToStaticMarkup(<RingkasanResi resi={resi} />);

    expect(html).toContain(resi[0].kode_qr);
    expect(html).toContain(resi[1].kode_qr);
  });
});
