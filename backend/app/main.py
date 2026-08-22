from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import get_settings
from app.routers import alamat, asumsi, auth, berita, dampak, demo, kiriman, lacak, lot, pengguna, riwayat, slot
from app.routers import master as master_router

app = FastAPI(
    title="Satu Muatan API",
    description="Sistem konsolidasi muatan & bukti mutu rantai pasok hortikultura.",
    version="0.1.0",
)

# CORS: origin frontend produksi + localhost. Jangan `*` di produksi (spec §3.3).
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().daftar_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (
    auth.router,
    pengguna.router,
    master_router.router,
    alamat.router,
    asumsi.router,
    kiriman.router,
    slot.router,
    lot.router,
    lacak.router,
    berita.router,
    dampak.router,
    riwayat.router,
    demo.router,
):
    app.include_router(r, prefix="/api")


class HealthOut(BaseModel):
    status: str


@app.get("/health", response_model=HealthOut, tags=["health"])
@app.get("/healthz", response_model=HealthOut, tags=["health"])
def healthz():
    return HealthOut(status="ok")
