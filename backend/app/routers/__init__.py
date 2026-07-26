"""Router FastAPI — kontrak beku. Handler Fase 0 = stub 501 bertipe benar;
implementasi = agent api-backend (Fase 1). Bentuk respons TIDAK BOLEH berubah
tanpa arsitek."""

from fastapi import HTTPException


def stub_fase_0():
    """Placeholder handler Fase 0."""
    raise HTTPException(status_code=501, detail="Stub Fase 0 — implementasi di Fase 1")
