"""Konfigurasi teknis aplikasi (env). Koefisien BISNIS tidak di sini —
semuanya hidup di tabel `konfigurasi` / `tier_kendaraan` (spec §4.1)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 127.0.0.1 (bukan "localhost"): di Windows, localhost dicoba lewat IPv6 dulu
    # dan bisa menggantung ~130 detik sebelum fallback ke IPv4 port-mapping Docker.
    database_url: str = "postgresql+psycopg://satu_muatan:satu_muatan_dev@127.0.0.1:5433/satu_muatan"
    jwt_secret: str = "ganti-di-produksi"
    jwt_kadaluarsa_menit: int = 60 * 24  # sesi login, bukan koefisien bisnis
    vendor_adapter: str = "MOCK"  # MOCK | DELIVEREE
    demo_mode: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def daftar_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
