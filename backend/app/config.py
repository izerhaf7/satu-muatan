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
    # K14 — reverse geocoding OPSIONAL. Kalau diisi, alamat dari peta dibaca
    # lewat Google Geocoding API; kalau kosong, sistem memakai tabel `wilayah`
    # miliknya sendiri. Dipanggil dari SERVER, jadi kuncinya tidak pernah masuk
    # browser dan tidak ikut ter-bundle ke aplikasi.
    google_maps_api_key: str = ""
    geo_provider_enabled: bool = True
    # Centroid wilayah bersifat kasar. Batas 25 km masih menoleransi titik
    # pedesaan di sekitar pusat kecamatan, tetapi menolak centroid kota lain.
    geo_local_max_distance_km: float = 25.0
    alamat_provider_timeout_detik: float = 4.0
    alamat_provider_response_max_bytes: int = 32_768
    alamat_saran_max_hasil: int = 5
    alamat_bias_radius_max_meter: float = 50_000
    alamat_rate_limit_per_jendela: int = 30
    alamat_rate_limit_jendela_detik: int = 60
    alamat_rate_limit_max_pengguna: int = 2_000

    @property
    def daftar_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
