# config/settings.py
"""Configuración del microservicio dedicacion-api.

Credenciales en .env (nunca en el repositorio). Parámetros funcionales
(consultas de sincronización, export) en config/config.yaml.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_DIR = Path(__file__).resolve().parent.parent
_CONFIG_YAML = Path(__file__).resolve().parent / "config.yaml"


class Settings(BaseSettings):
    """Variables de entorno del servicio."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- API ---
    api_host: str = "127.0.0.1"
    api_port: int = 8090
    service_name: str = "dedicacion-api"
    service_version: str = "1.0.0"
    log_level: str = "INFO"

    # --- PostgreSQL (aplicación) ---
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_db: str = "dedicacion"
    pg_user: str = "dedicacion_app"
    pg_password: str = ""
    pg_sslmode: str = "prefer"  # "require" en Azure

    # --- PostgreSQL (admin: crea la BBDD si no existe) ---
    pg_admin_user: str = "postgres"
    pg_admin_password: str = ""
    pg_admin_db: str = "postgres"

    # --- Sigrid API (Function App) ---
    sigrid_api_base_url: str = ""
    sigrid_api_function_key: str = ""
    sigrid_api_database: str = "ruesma"
    sigrid_api_timeout_s: float = 60.0
    sigrid_max_rows: int = 5000

    # porcentajes-transfer (registro en Sigrid)
    transfer_base_url: str = "http://127.0.0.1:8006"
    transfer_timeout_s: float = 180.0

    # ------------------------------------------------------------------
    @property
    def database_url(self) -> str:
        """URL SQLAlchemy (driver psycopg 3) de la BBDD de aplicación."""
        return (
            f"postgresql+psycopg://{quote_plus(self.pg_user)}:"
            f"{quote_plus(self.pg_password)}@{self.pg_host}:{self.pg_port}/"
            f"{self.pg_db}?sslmode={self.pg_sslmode}"
        )

    @property
    def sigrid_configurado(self) -> bool:
        return bool(self.sigrid_api_base_url and self.sigrid_api_function_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def cargar_config() -> dict[str, Any]:
    """Carga config/config.yaml (consultas de sincronización, export)."""
    with _CONFIG_YAML.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)
