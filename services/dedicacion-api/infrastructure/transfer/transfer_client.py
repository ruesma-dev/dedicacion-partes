# infrastructure/transfer/transfer_client.py
"""Cliente HTTP de porcentajes-transfer (preflight / ejecutar, universo de
postventa, F-025, y universo VAR, F-039)."""
from __future__ import annotations

from typing import Any

import httpx

from config.settings import Settings
from domain.errors import UniversoPostventaNoDisponible, UniversoVarNoDisponible
from domain.models import PartidaVar, ResultadoUniverso, ResultadoUniversoVar


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

    def universo_postventa(
        self, empresa: int, obras: list[dict[str, Any]]
    ) -> ResultadoUniverso:
        """Universo de postventa de `empresa` (`UniversoPostventaGateway`).

        Si el transfer no responde, o responde sin `ok: true` o sin `obras`,
        no hay universo: `UniversoPostventaNoDisponible` (F-025, R15)."""
        r = self._post("/api/postventa/universo",
                       {"empresa": empresa, "obras": obras})
        if r.get("ok") is not True or "obras" not in r:
            causa = r.get("error") or "la respuesta del transfer no trae obras"
            raise UniversoPostventaNoDisponible(
                f"universo de postventa no disponible: {causa}")
        return ResultadoUniverso(ides=frozenset(o["ide"] for o in r["obras"]),
                                 motivo=r.get("motivo"))

    def universo_var(self, empresa: int) -> ResultadoUniversoVar:
        """Universo VAR de `empresa` (`UniversoVarGateway`, F-039,
        docs/ARCHITECTURE.md#regla-var).

        Si el transfer no responde, o responde sin `ok: true` o sin
        `partidas`, no hay universo: `UniversoVarNoDisponible` (R16)."""
        r = self._post("/api/var/universo", {"empresa": empresa})
        if r.get("ok") is not True or "partidas" not in r:
            causa = (r.get("error")
                     or "la respuesta del transfer no trae partidas")
            raise UniversoVarNoDisponible(
                f"universo VAR no disponible: {causa}")
        obra = r.get("obra_var") or {}
        return ResultadoUniversoVar(
            obra_ide=obra.get("ide"), obra_cod=obra.get("codigo"),
            empresa=obra.get("empresa"), motivo=r.get("motivo"),
            partidas=tuple(PartidaVar(ide=p["ide"], cod=p["cod"],
                                      res=p.get("res"))
                           for p in r["partidas"]))
