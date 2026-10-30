# infrastructure/transfer/transfer_client.py
"""Cliente HTTP de porcentajes-transfer (preflight / ejecutar, universo de
postventa, F-025, universo VAR, F-039, y los % que ya hay en Sigrid,
F-054)."""
from __future__ import annotations

from dataclasses import fields
from typing import Any

import httpx

from config.settings import Settings
from domain.errors import (
    PorcentajesSigridNoDisponible,
    PropuestaNoDisponible,
    UniversoPostventaNoDisponible,
    UniversoVarNoDisponible,
)
from domain.models import (
    LineaSigridTraida,
    PartidaVar,
    ResultadoExistentes,
    ResultadoUniverso,
    ResultadoUniversoVar,
)

#: Los campos de una línea traída (F-054): lo demás que mande el transfer
#: se ignora.
_CAMPOS_TRAIDA = tuple(f.name for f in fields(LineaSigridTraida))


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

    def preflight_lote(self, peticiones: list[dict], completo: bool = False
                       ) -> dict[str, Any]:
        """F-055 (R26): el preflight de varias obras en una llamada
        (`POST /api/registro/preflight-lote`): `{ok, obras}`. F-054 (R31):
        con `completo`, también `sobrantes`; la clave solo viaja si es
        `true` (un transfer viejo la ignora y responde como hoy)."""
        return self._post("/api/registro/preflight-lote",
                          {"peticiones": peticiones,
                           **({"completo": True} if completo else {})})

    def poner_a_cero(self, empresa: int, ano: int, mes: int,
                     lineas: list[dict]) -> dict[str, Any]:
        """F-054 (R35): pone a 0 las sobrantes confirmadas (`POST
        /api/registro/poner-a-cero`): `{ok, puestas, omitidas}`. Sin `ok:
        true`, `RuntimeError` con el motivo: no se sigue escribiendo."""
        r = self._post("/api/registro/poner-a-cero",
                       {"empresa": empresa, "ano": ano, "mes": mes,
                        "lineas": lineas})
        if r.get("ok") is not True:
            raise RuntimeError("no se pudieron poner a 0 las líneas "
                               f"sobrantes: {r.get('error') or r}")
        return r

    def ejecutar(self, payload: dict) -> dict[str, Any]:
        return self._post("/api/registro/ejecutar", payload)

    def propuesta_partidas(self, payload: dict) -> dict[str, Any]:
        """Catálogo y partida propuesta de unas líneas (F-050, R17). Sin
        `ok: true` o sin `propuestas`: `PropuestaNoDisponible`."""
        r = self._post("/api/partidas/propuesta", payload)
        if r.get("ok") is not True or "propuestas" not in r:
            causa = (r.get("error")
                     or "la respuesta del transfer no trae propuestas")
            raise PropuestaNoDisponible(
                f"propuesta de partidas no disponible: {causa}")
        return r

    def propuesta_lote(self, peticiones: list[dict]) -> dict[str, Any]:
        """F-055 (R31, R34): las propuestas de varias obras de un periodo
        (`POST /api/partidas/propuesta-lote`): `{ok, obras}`. Sin `ok: true`
        o sin `obras`: `PropuestaNoDisponible` (R33)."""
        r = self._post("/api/partidas/propuesta-lote",
                       {"peticiones": peticiones})
        if r.get("ok") is not True or not isinstance(r.get("obras"), list):
            causa = r.get("error") or "la respuesta del transfer no trae obras"
            raise PropuestaNoDisponible(
                f"propuesta de partidas no disponible: {causa}")
        return r

    def porcentajes_existentes(
        self, empresa: int, anio: int, mes: int, obras: list[dict[str, Any]]
    ) -> ResultadoExistentes:
        """F-054 (R3-R12; `PorcentajesSigridGateway`): las líneas mensuales
        del periodo de `empresa` en Sigrid, traducidas por el transfer
        (`POST /api/porcentajes/existentes`). `obras`, las que admiten
        postventa. Sin `ok: true` o sin `lineas` (caído, lectura que falla
        o truncada): `PorcentajesSigridNoDisponible` con el motivo."""
        r = self._post("/api/porcentajes/existentes",
                       {"empresa": empresa, "ano": anio, "mes": mes,
                        "obras": obras})
        if r.get("ok") is not True or not isinstance(r.get("lineas"), list):
            causa = r.get("error") or "la respuesta del transfer no trae líneas"
            raise PorcentajesSigridNoDisponible(
                f"las líneas de Sigrid no están disponibles: {causa}")
        return ResultadoExistentes(
            lineas_leidas=int(r.get("lineas_leidas") or 0),
            excluidas_pruebas=int(r.get("excluidas_pruebas") or 0),
            motivo_postventa=r.get("motivo_postventa"),
            motivo_var=r.get("motivo_var"),
            lineas=tuple(LineaSigridTraida(**{k: x[k] for k in _CAMPOS_TRAIDA
                                              if k in x})
                         for x in r["lineas"]))

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
