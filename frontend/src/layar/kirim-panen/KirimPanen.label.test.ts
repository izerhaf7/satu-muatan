import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

const sumber = readFileSync(new URL("../KirimPanen.tsx", import.meta.url), "utf8").replace(/\r\n/g, "\n");

describe("penanda isian wajib Kirim Panen", () => {
  it("menandai Komoditas sebagai Wajib", () => {
    expect(sumber).toMatch(/Komoditas\s*<span[^>]*>Wajib<\/span>/);
  });

  it.each(["Volume (kg)", "Tanggal siap"])("menandai %s sebagai Wajib", (label) => {
    expect(sumber).toContain(`label="${label}"\n            penanda="Wajib"`);
  });
});
