import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

const sumber = readFileSync(new URL("./PetaPilihTitik.tsx", import.meta.url), "utf8");

describe("layout konfirmasi titik", () => {
  it("menjaga kedua aksi 48 px di atas navigasi bawah pada layar 360 px", () => {
    const panelPending = sumber.match(/\{pending && \([\s\S]*?\n\s*\)\}/)?.[0] ?? "";

    expect(panelPending).toContain("scroll-mb-28");
    expect(panelPending).toContain("Konfirmasi titik ini");
    expect(panelPending).toContain("Batalkan perubahan");
    expect(panelPending.match(/<Tombol/g)).toHaveLength(2);
  });
});
