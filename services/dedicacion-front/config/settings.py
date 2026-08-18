# config/settings.py
"""Configuración del microservicio dedicacion-front."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    front_host: str = "127.0.0.1"
    front_port: int = 8080
    service_name: str = "dedicacion-front"
    service_version: str = "1.0.0"
    log_level: str = "INFO"

    # URL interna del backend dedicacion-api
    api_base_url: str = "http://127.0.0.1:8090"
    api_timeout_s: float = 120.0

    # Usuario por defecto cuando no hay Easy Auth (desarrollo local)
    default_user: str = "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
