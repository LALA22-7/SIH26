"""Application configuration loaded from environment variables."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ─────────────────────────────────────────────
    database_url: str = (
        "postgresql+asyncpg://cyclone:cyclone_secret@localhost:5432/cyclonewatch"
    )
    database_sync_url: str = (
        "postgresql+psycopg2://cyclone:cyclone_secret@localhost:5432/cyclonewatch"
    )

    # ── Application ──────────────────────────────────────────
    debug: bool = True
    api_version: str = "v1"

    # ── CORS ─────────────────────────────────────────────────
    cors_origins: str = "*"

    # ── Data paths ───────────────────────────────────────────
    data_root: str = "/data"
    demo_data_root: str = "/data/demo"

    # ── ML ───────────────────────────────────────────────────
    ml_package_path: str = "/ml"
    ml_force_stub: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
