# infrastructure/transfer/transfer_client.py
"""Cliente HTTP de porcentajes-transfer (preflight / ejecutar)."""
from __future__ import annotations

from typing import Any

import httpx

from config.settings import Settings


class TransferClient:
    def __init__(self, settings: Settings) -> None:
        self._base = settings.transfer_base_url.rstrip("/")
        self._timeout = settings.transfer_timeout_s

    def _post(self, ruta: str, payload: dict) -> dict[str, Any]:
        try:
            r = httpx.post(f"{self._base}{ruta}", json=payload,
                           timeout=self._timeout)
        except httpx.HTTPError as exc:
            return {"ok": False, "error": f"transfer inaccesible: {exc}"}
        try:
            cuerpo = r.json()
        except ValueError:
            return {"ok": False,
                    "error": f"transfer HTTP {r.status_code}: {r.text[:200]}"}
        if r.status_code >= 400 and "error" not in cuerpo:
            cuerpo = {"ok": False, "error": f"HTTP {r.status_code}"}
        return cuerpo

    def preflight(self, payload: dict) -> dict[str, Any]:
        return self._post("/api/registro/preflight", payload)

    def ejecutar(self, payload: dict) -> dict[str, Any]:
        return self._post("/api/registro/ejecutar", payload)
