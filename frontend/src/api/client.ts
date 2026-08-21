/** Client API bertipe — satu-satunya jalur frontend ke backend.
 *  Tipe digenerate dari kontrak/openapi.yaml (kontrak beku). */

import type { paths } from "../../kontrak/types.ts";

export type { components, paths } from "../../kontrak/types.ts";

const BASE_URL = import.meta.env.VITE_API_URL ?? "";

let tokenSaatIni: string | null = null;

export function setToken(token: string | null): void {
  tokenSaatIni = token;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(`API ${status}`);
  }
}

/** Panggilan mentah; hook TanStack Query per layar dibangun di atas ini (Fase 1+). */
export async function api<T>(path: keyof paths | (string & {}), init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${String(path)}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(tokenSaatIni ? { Authorization: `Bearer ${tokenSaatIni}` } : {}),
      ...init?.headers,
    },
  });
  const body = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, body);
  return body as T;
}
