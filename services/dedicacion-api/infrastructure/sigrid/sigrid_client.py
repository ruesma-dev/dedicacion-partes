# infrastructure/sigrid/sigrid_client.py
"""Adaptador de lectura contra la Function App sigrid-api.

Único punto de acceso permitido al SQL Server on-prem de Sigrid:
POST {base}/api/sql/read  con  { database, sql, parameters, max_rows,
timeout_seconds } y cabecera x-functions-key.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from config.settings import Settings
from domain.errors import SigridError, SigridNoConfigurado

logger = logging.getLogger(__name__)


class SigridApiClient:
    """Implementa el puerto SigridGateway (solo lectura)."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def leer(self, sql: str) -> list[dict[str, Any]]:
        cfg = self._settings
        if not cfg.sigrid_configurado:
            raise SigridNoConfigurado(
                "SIGRID_API_BASE_URL / SIGRID_API_FUNCTION_KEY sin configurar"
            )
        url = cfg.sigrid_api_base_url.rstrip("/") + "/api/sql/read"
        payload = {
            "database": cfg.sigrid_api_database,
            "sql": sql,
            "parameters": [],
            "max_rows": cfg.sigrid_max_rows,
            "timeout_seconds": int(cfg.sigrid_api_timeout_s),
        }
        headers = {"x-functions-key": cfg.sigrid_api_function_key}
        try:
            respuesta = httpx.post(
                url,
                json=payload,
                headers=headers,
                timeout=cfg.sigrid_api_timeout_s + 15.0,
            )
        except httpx.HTTPError as exc:
            raise SigridError(f"Error de red contra sigrid-api: {exc}") from exc

        if respuesta.status_code != 200:
            raise SigridError(
                f"sigrid-api HTTP {respuesta.status_code}: {respuesta.text[:400]}"
            )
        cuerpo = respuesta.json()
        if not cuerpo.get("ok", False):
            raise SigridError(f"sigrid-api ok=false: {cuerpo}")
        if cuerpo.get("truncated"):
            raise SigridError(
                "Resultado truncado por max_rows "
                f"({cfg.sigrid_max_rows}); ajustar SIGRID_MAX_ROWS o paginar "
                "la consulta en config.yaml"
            )
        columnas: list[str] = cuerpo.get("columns", [])
        filas: list[list[Any]] = cuerpo.get("rows", [])
        logger.info(
            "sigrid-api: %s filas, columnas=%s", cuerpo.get("row_count"), columnas
        )
        return [dict(zip(columnas, fila)) for fila in filas]
