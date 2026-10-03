# interface_adapters/api/app.py
"""API HTTP de porcentajes-transfer.

  POST /api/registro/preflight  -> analiza y devuelve qué se haría
  POST /api/registro/ejecutar   -> escribe en Sigrid (con pisar_claves)
  POST /api/postventa/universo  -> obras de una empresa que admiten postventa
                                   (ARCHITECTURE.md#regla-p5; solo lee)
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
from application.services.reglas_porcentajes import (
    clave_conflicto, empresa_valida,
)
from application.services.universo_postventa import UniversoPostventa
from domain.errores import EmpresasMezcladas
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
    # Recurso del trabajador (ARCHITECTURE.md#regla-recurso). Sin él la línea
    # se omite con motivo. El ide de la ficha de empleado salió del contrato
    # en F-026: si un cliente viejo lo manda, Pydantic lo ignora (no es un
    # 422).
    recurso_ide: Optional[int] = None
    dni: Optional[str] = None
    nombre: Optional[str] = None
    categoria: Optional[str] = None
    es_postventa: bool = False
    paride: Optional[int] = None        # override manual de la partida
    partida_cod: Optional[str] = None
    # Empresa a la que se imputa (ARCHITECTURE.md#regla-empresa). Opcional A
    # PROPÓSITO: una línea sin empresa tiene que llegar al pipeline para
    # omitirse con motivo, no morir aquí en un 422 que no deja traza.
    empresa: Optional[int] = None


class PeticionIn(BaseModel):
    obra: ObraIn
    lineas: list[LineaIn] = Field(default_factory=list)
    pisar_claves: list[str] = Field(default_factory=list)
    usuario: Optional[str] = None


class UniversoIn(BaseModel):
    """Petición del universo de postventa: UNA empresa y sus obras.

    `empresa` es opcional a propósito: sin ella se responde 422 con motivo,
    no con el error genérico de validación."""

    empresa: Optional[int] = None
    obras: list[ObraIn] = Field(default_factory=list)


def _empresas_mezcladas(exc: EmpresasMezcladas) -> JSONResponse:
    """Una petición con líneas de varias empresas es un dato de entrada
    inválido (422), no un fallo de Sigrid (502): no se ha leído nada."""
    logger.warning("peticion rechazada: %s", exc)
    return JSONResponse(status_code=422,
                        content={"ok": False, "error": str(exc)})


def build_app(settings) -> FastAPI:
    app = FastAPI(title="Porcentajes -> Sigrid (transfer)", version="1.0.0")

    cliente = SigridWriteClient(
        base_url=settings.sigrid_api_base_url,
        function_key=settings.sigrid_api_function_key,
        database=settings.sigrid_api_database,
        timeout_s=settings.sigrid_api_timeout_s,
        max_statements=settings.sigrid_max_statements,
        tip_parte=settings.tip_parte_trabajo,
        est_parte=settings.est_parte_activo,
    )
    pipeline = RegistroPipeline(cliente=cliente, settings=settings)
    universo = UniversoPostventa(cliente=cliente, settings=settings)

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
                "acciones": [asdict(a) | {"clave": clave_conflicto(a)}
                             for a in pf.acciones],
                "conflictos": [asdict(c) for c in pf.conflictos],
                "resumen": {"escribir": pf.n_escribir, "omitir": pf.n_omitir,
                            "ya_registrado": pf.n_ya,
                            "conflictos": len(pf.conflictos)},
            }
        except EmpresasMezcladas as exc:
            return _empresas_mezcladas(exc)
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
        except EmpresasMezcladas as exc:
            return _empresas_mezcladas(exc)
        except Exception as exc:                # noqa: BLE001
            logger.exception("ejecutar fallo")
            return JSONResponse(status_code=502,
                                content={"ok": False, "error": str(exc)})

    @app.post("/api/postventa/universo")
    async def universo_postventa(p: UniversoIn):
        if not empresa_valida(p.empresa):
            logger.warning("universo rechazado: empresa %r", p.empresa)
            return JSONResponse(status_code=422, content={
                "ok": False,
                "error": f"empresa no válida: {p.empresa!r}"})
        try:
            obras = [ObraEntrada(ide=o.ide, codigo=o.codigo, nombre=o.nombre)
                     for o in p.obras]
            return {"ok": True, **universo.calcular(p.empresa, obras)}
        except Exception as exc:                # noqa: BLE001
            logger.exception("universo de postventa fallo")
            return JSONResponse(status_code=502,
                                content={"ok": False, "error": str(exc)})

    return app
