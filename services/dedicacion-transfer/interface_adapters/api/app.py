# interface_adapters/api/app.py
"""API HTTP de porcentajes-transfer.

  POST /api/registro/preflight  -> analiza y devuelve qué se haría
  POST /api/registro/ejecutar   -> escribe en Sigrid (con pisar_claves)
  GET  /health
"""
from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import LineaEntrada, ObraEntrada
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient

logger = logging.getLogger(__name__)


# ----------------------------- esquemas ----------------------------- #

class ObraIn(BaseModel):
    ide: Optional[int] = None
    codigo: Optional[str] = None
    nombre: Optional[str] = None


class LineaIn(BaseModel):
    registro_id: int
    ano: int
    mes: int
    porcentaje: float                   # sobre 1: 40 % -> 0.4
    empleado_ide: Optional[int] = None
    recurso_ide: Optional[int] = None
    dni: Optional[str] = None
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    es_postventa: bool = False
    paride: Optional[int] = None        # override manual de la partida
    partida_cod: Optional[str] = None


class PeticionIn(BaseModel):
    obra: ObraIn
    lineas: list[LineaIn] = Field(default_factory=list)
    pisar_claves: list[str] = Field(default_factory=list)
    usuario: Optional[str] = None


def build_app(settings) -> FastAPI:
    app = FastAPI(title="Porcentajes -> Sigrid (transfer)", version="1.0.0")

    cliente = SigridWriteClient(
        base_url=settings.sigrid_api_base_url,
        function_key=settings.sigrid_api_function_key,
        database=settings.sigrid_api_database,
        empresa=settings.sigrid_empresa,
        timeout_s=settings.sigrid_api_timeout_s,
        max_statements=settings.sigrid_max_statements,
        tip_parte=settings.tip_parte_trabajo,
        est_parte=settings.est_parte_activo,
    )
    pipeline = RegistroPipeline(cliente=cliente, settings=settings)

    def _dominio(p: PeticionIn):
        obra = ObraEntrada(ide=p.obra.ide, codigo=p.obra.codigo,
                           nombre=p.obra.nombre)
        lineas = [LineaEntrada(**l.model_dump()) for l in p.lineas]
        return obra, lineas

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "ok": True,
            "servicio": "porcentajes-transfer",
            "modo_pruebas": settings.obra_pruebas_forzar,
            "obra_pruebas": settings.obra_pruebas_cod,
            "database": settings.sigrid_api_database,
            "postventa_registrar": settings.postventa_registrar,
        }

    @app.post("/api/registro/preflight")
    async def preflight(p: PeticionIn):
        try:
            obra, lineas = _dominio(p)
            pf = pipeline.preflight(obra=obra, lineas=lineas)
            obra_pv = getattr(pf, "obra_postventa", None)
            return {
                "ok": True,
                "obra_destino": asdict(pf.obra_destino),
                "obra_postventa": asdict(obra_pv) if obra_pv else None,
                "capitulo_postventa": getattr(pf, "capitulo_postventa",
                                              None),
                "partidas_obra": getattr(pf, "partidas_obra", []),
                "partidas_postventa": getattr(pf, "partidas_postventa", []),
                "forzada_pruebas": pf.forzada_pruebas,
                "partes": [asdict(x) for x in pf.partes],
                "acciones": [asdict(a) | {"clave": a.clave_conflicto}
                             for a in pf.acciones],
                "conflictos": [asdict(c) for c in pf.conflictos],
                "resumen": {"escribir": pf.n_escribir, "omitir": pf.n_omitir,
                            "ya_registrado": pf.n_ya,
                            "conflictos": len(pf.conflictos)},
            }
        except Exception as exc:                # noqa: BLE001
            logger.exception("preflight fallo")
            return JSONResponse(status_code=502,
                                content={"ok": False, "error": str(exc)})

    @app.post("/api/registro/ejecutar")
    async def ejecutar(p: PeticionIn):
        try:
            obra, lineas = _dominio(p)
            r = pipeline.ejecutar(obra=obra, lineas=lineas,
                                  pisar_claves=set(p.pisar_claves),
                                  usuario=p.usuario)
            return {
                "ok": r.ok,
                "obra_destino": asdict(r.obra_destino),
                "forzada_pruebas": r.forzada_pruebas,
                "partes": [asdict(x) for x in r.partes],
                "escritas": r.escritas,
                "omitidas": r.omitidas,
                "ya_registradas": r.ya_registradas,
                "pisadas": r.pisadas,
                "borradas": r.borradas,
                "pendientes_confirmacion": [asdict(c) for c in
                                            r.pendientes_confirmacion],
                "error": r.error,
            }
        except Exception as exc:                # noqa: BLE001
            logger.exception("ejecutar fallo")
            return JSONResponse(status_code=502,
                                content={"ok": False, "error": str(exc)})

    return app
