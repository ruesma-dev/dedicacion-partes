# interface_adapters/api/app.py
"""API HTTP de porcentajes-transfer.

  POST /api/registro/preflight  -> analiza y devuelve qué se haría
  POST /api/registro/preflight-lote -> el preflight de varias obras con las
                                   lecturas agrupadas (F-055 R19; solo lee)
  POST /api/registro/ejecutar   -> escribe en Sigrid (con pisar_claves)
  POST /api/postventa/universo  -> obras de una empresa que admiten postventa
                                   (ARCHITECTURE.md#regla-p5; solo lee)
  POST /api/var/universo        -> obra VAR de una empresa y sus partidas VAR
                                   (ARCHITECTURE.md#regla-var; solo lee)
  POST /api/partidas/propuesta  -> catálogo con su mayor y partida propuesta
                                   de cada línea (ARCHITECTURE.md
                                   #regla-partida; solo lee)
  POST /api/partidas/propuesta-lote -> las propuestas de varias obras de un
                                   periodo, con las lecturas agrupadas
                                   (F-055 R34; solo lee)
  GET  /health
"""
from __future__ import annotations

import logging
from dataclasses import asdict
from typing import Any, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from application.pipelines.registro_lote import RegistroLote
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.reglas_porcentajes import (
    clave_conflicto, empresa_valida,
)
from application.services.universo_postventa import UniversoPostventa
from application.services.universo_var import UniversoVar
from domain.errores import EmpresasMezcladas
from domain.models.registro_models import (
    ContextoRachas, IncidenciaEntrada, LineaEntrada, ObraEntrada,
)
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
    # Partida VAR de una entrada `VAR-NN` (ARCHITECTURE.md#regla-var).
    var_paride: Optional[int] = None
    # F-055 (R16): propuesta guardada de una línea automática.
    propuesta_paride: Optional[int] = None
    propuesta_cod: Optional[str] = None
    propuesta_res: Optional[str] = None
    propuesta_metodo: Optional[str] = None
    propuesta_origen: Optional[str] = None
    # F-051 (R14): `hmores.ide` de lo ya registrado (opcional: sin él, como
    # hasta ahora, por `synckey`).
    hmores_ide: Optional[int] = None


class IncidenciaIn(BaseModel):
    """F-030 (R23): una incidencia de la obra. Todo lo que puede faltar es
    opcional A PROPÓSITO, como en `LineaIn`: llega al pipeline y se omite
    con motivo, no muere en un 422."""
    id: int
    recurso_ide: int | None = None
    empresa: int | None = None
    codigo: str
    ano: int
    mes: int
    desde: int | None = None
    hasta: int | None = None
    paride: int | None = 0
    # Anexo R30 (R39): la traza de la api de una ya registrada.
    hmores_ide_ini: int | None = None
    hmores_ide_fin: int | None = None
    dia_ini: int | None = None
    dia_fin: int | None = None
    # F-062 (R15, R24): la obra de la incidencia y, si su `fin` es un `CIZ`
    # ajeno que movimos, su día original.
    obra_ide: int | None = None
    dia_fin_antes: int | None = None


class PeticionIn(BaseModel):
    obra: ObraIn
    lineas: list[LineaIn] = Field(default_factory=list)
    # F-030 (R23): por defecto vacía; sin ellas, la petición de siempre.
    incidencias: list[IncidenciaIn] = Field(default_factory=list)
    # F-062 (R12, R17, R24): el contexto del mes; vacío, la de F-030.
    incidencias_mes: list[IncidenciaIn] = Field(default_factory=list)
    cierres_recursos: list[int] = Field(default_factory=list)
    quitadas: list[IncidenciaIn] = Field(default_factory=list)
    pisar_claves: list[str] = Field(default_factory=list)
    usuario: Optional[str] = None


class LoteIn(BaseModel):
    """`POST /api/registro/preflight-lote` (F-055 R19): varias peticiones
    de preflight, una por obra."""

    peticiones: list[PeticionIn] = Field(default_factory=list)


class UniversoIn(BaseModel):
    """Petición del universo de postventa: UNA empresa y sus obras.

    `empresa` es opcional a propósito: sin ella se responde 422 con motivo,
    no con el error genérico de validación."""

    empresa: int | None = None
    obras: list[ObraIn] = Field(default_factory=list)


class UniversoVarIn(BaseModel):
    """Petición del universo VAR (F-039): UNA empresa. Opcional por lo
    mismo que en `UniversoIn`: sin ella, 422 con motivo."""

    empresa: int | None = None


class LineaPropuestaIn(BaseModel):
    """Una línea del cuadrante cuya partida se propone (F-050, R8)."""

    clave: str
    recurso_ide: int | None = None
    nombre: str | None = None
    categoria: str | None = None
    es_postventa: bool = False


class PropuestaIn(BaseModel):
    """Petición de `POST /api/partidas/propuesta` (F-050, R8). `empresa`
    opcional por lo mismo que en `UniversoIn`: sin ella, 422 con motivo."""

    empresa: int | None = None
    obra: ObraIn
    ano: int
    mes: int
    lineas: list[LineaPropuestaIn] = Field(default_factory=list)


class PropuestaLoteIn(BaseModel):
    """`POST /api/partidas/propuesta-lote` (F-055 R34): varias peticiones
    de propuesta, todas del mismo `ano` y `mes` (si no, 422)."""

    peticiones: list[PropuestaIn] = Field(default_factory=list)


def _empresas_mezcladas(exc: EmpresasMezcladas) -> JSONResponse:
    """Una petición con líneas de varias empresas es un dato de entrada
    inválido (422), no un fallo de Sigrid (502): no se ha leído nada."""
    logger.warning("peticion rechazada: %s", exc)
    return JSONResponse(status_code=422,
                        content={"ok": False, "error": str(exc)})


#: F-030 (R31, design §6): lo que se publica de cada línea de incidencia.
CLAVES_INCIDENCIA = ("id", "rol", "accion", "fecha_int", "hora_codigo",
                     "paride", "parte_cod", "hmores_ide", "motivo")


def _con_incidencias(respuesta: dict, incidencias: list) -> dict:
    """F-030 (R31): `incidencias` solo si la petición las traía; sin
    ellas, la respuesta es la de siempre. Anexo R30 (R46): una `editar`
    publica además `fec_antes`; las demás, las claves de siempre."""
    if incidencias:
        respuesta["incidencias"] = [
            {**{k: getattr(a, k) for k in CLAVES_INCIDENCIA},
             **({"fec_antes": a.fec_antes} if a.accion == "editar" else {}),
             **({"ajena": True} if a.ajena else {})}
            for a in incidencias]
    return respuesta


#: F-062 (R22): lo que no se publica de un `CierreRacha` (es para escribir).
_CIERRE_PRIVADO = ("synckey", "hmoide", "obride", "cenide", "paride",
                   "caaide", "hora_ide", "pre")


def _con_rachas(respuesta: dict, r) -> dict:
    """F-062 (R22): `rachas`, `cierres_racha` (sin lo que es para escribir)
    y `no_coincide`, solo si la petición traía las claves nuevas."""
    respuesta["rachas"] = [asdict(x) for x in getattr(r, "rachas", [])]
    respuesta["cierres_racha"] = [
        {k: v for k, v in asdict(x).items() if k not in _CIERRE_PRIVADO}
        for x in getattr(r, "cierres_racha", [])]
    respuesta["no_coincide"] = [asdict(x)
                                for x in getattr(r, "no_coincide", [])]
    return respuesta


def _respuesta_preflight(pf, con_rachas: bool = False) -> dict:
    """La respuesta de `POST /api/registro/preflight` (y de cada obra de
    `POST /api/registro/preflight-lote`) para un `Preflight`; con las
    claves de F-062 si la petición traía su contexto (`con_rachas`)."""
    obra_pv = getattr(pf, "obra_postventa", None)
    respuesta = _con_incidencias({
        "ok": True,
        "obra_destino": asdict(pf.obra_destino),
        "obra_postventa": asdict(obra_pv) if obra_pv else None,
        "capitulo_postventa": getattr(pf, "capitulo_postventa", None),
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
    }, pf.incidencias)
    return _con_rachas(respuesta, pf) if con_rachas else respuesta


def build_app(settings) -> FastAPI:
    app = FastAPI(title="Porcentajes -> Sigrid (transfer)", version="1.0.0")

    cliente = SigridWriteClient(
        base_url=settings.sigrid_api_base_url,
        function_key=settings.sigrid_api_function_key,
        database=settings.sigrid_api_database,
        timeout_s=settings.sigrid_api_timeout_s,
        max_statements=settings.sigrid_max_statements,
        max_rows=settings.sigrid_max_rows,
        tip_parte=settings.tip_parte_trabajo,
        est_parte=settings.est_parte_activo,
    )
    pipeline = RegistroPipeline(cliente=cliente, settings=settings)
    universo = UniversoPostventa(cliente=cliente, settings=settings)
    universo_var = UniversoVar(cliente=cliente, settings=settings)

    def _dominio(p: PeticionIn) -> tuple:
        """`(obra, lineas)` y, si las trae, sus incidencias (F-030) y el
        contexto del mes (F-062, `ContextoRachas`)."""
        obra = ObraEntrada(ide=p.obra.ide, codigo=p.obra.codigo,
                           nombre=p.obra.nombre)
        lineas = [LineaEntrada(**l.model_dump()) for l in p.lineas]
        contexto = _contexto(p)
        if not p.incidencias and contexto is None:
            return obra, lineas
        incidencias = [IncidenciaEntrada(**x.model_dump())
                       for x in p.incidencias]
        if contexto is None:
            return obra, lineas, incidencias
        return obra, lineas, incidencias, contexto

    def _contexto(p: PeticionIn) -> ContextoRachas | None:
        """F-062 (R24): el contexto del mes; sin ninguna clave nueva, None
        (la petición y la respuesta de F-030)."""
        if not (p.incidencias_mes or p.cierres_recursos or p.quitadas):
            return None
        return ContextoRachas(
            incidencias_mes=[IncidenciaEntrada(**x.model_dump())
                             for x in p.incidencias_mes],
            cierres_recursos=[int(r) for r in p.cierres_recursos],
            quitadas=[IncidenciaEntrada(**x.model_dump())
                      for x in p.quitadas])

    def _kw_incidencias(resto: list) -> dict:
        """Sin incidencias, la llamada de siempre (R2)."""
        return {"incidencias": resto[0]} if resto else {}

    def _pipeline(resto: list) -> RegistroPipeline:
        """F-062 (R24): con el contexto del mes, el pipeline que lo lleva."""
        return pipeline.con_contexto(resto[1]) if len(resto) > 1 else pipeline

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
            obra, lineas, *resto = _dominio(p)
            pf = _pipeline(resto).preflight(obra=obra, lineas=lineas,
                                            **_kw_incidencias(resto))
            return _respuesta_preflight(pf, len(resto) > 1)
        except EmpresasMezcladas as exc:
            return _empresas_mezcladas(exc)
        except Exception as exc:                # noqa: BLE001
            logger.exception("preflight fallo")
            return JSONResponse(status_code=502,
                                content={"ok": False, "error": str(exc)})

    @app.post("/api/registro/preflight-lote")
    def preflight_lote(p: LoteIn):
        """F-055 (R19, R24, R25): síncrona, en el threadpool. Por petición,
        la forma de `/api/registro/preflight` o `{ok: false, error}`; una
        lectura agrupada que falla, 502."""
        try:
            resultados = RegistroLote(cliente=cliente,
                                      settings=settings).preflight(
                [_dominio(x) for x in p.peticiones])
        except Exception as exc:                # noqa: BLE001
            logger.exception("preflight en lote fallo")
            return JSONResponse(status_code=502,
                                content={"ok": False, "error": str(exc)})
        obras = []
        for x, r in zip(p.peticiones, resultados):
            if isinstance(r, Exception):
                logger.warning("preflight en lote: una obra falla: %s", r)
                obras.append({"ok": False, "error": str(r)})
            else:
                obras.append(_respuesta_preflight(
                    r, _contexto(x) is not None))
        return {"ok": True, "obras": obras}

    @app.post("/api/registro/ejecutar")
    async def ejecutar(p: PeticionIn):
        try:
            obra, lineas, *resto = _dominio(p)
            r = _pipeline(resto).ejecutar(obra=obra, lineas=lineas,
                                          pisar_claves=set(p.pisar_claves),
                                          usuario=p.usuario,
                                          **_kw_incidencias(resto))
            respuesta = _con_incidencias({
                "ok": r.ok,
                "obra_destino": asdict(r.obra_destino),
                "forzada_pruebas": r.forzada_pruebas,
                "partes": [asdict(x) for x in r.partes],
                "escritas": r.escritas,
                "omitidas": r.omitidas,
                "ya_registradas": r.ya_registradas,
                "pisadas": r.pisadas,
                # F-051 (R6, R16, R18): `borradas` siempre 0; lo editado y
                # lo puesto a 0, con su antes y después, y el `hmores.ide`
                # de cada ya registrada.
                "borradas": r.borradas,
                "editadas": r.editadas,
                "a_cero": r.a_cero,
                "ya_registradas_ide": r.ya_registradas_ide,
                "pendientes_confirmacion": [asdict(c) for c in
                                            r.pendientes_confirmacion],
                "error": r.error,
            }, r.incidencias)
            return _con_rachas(respuesta, r) if len(resto) > 1 else respuesta
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
        except Exception as exc:
            logger.exception("universo de postventa fallo")
            return JSONResponse(status_code=502,
                                content={"ok": False, "error": str(exc)})

    @app.post("/api/partidas/propuesta")
    async def propuesta_de_partidas(p: PropuestaIn):
        """F-050 (R8): solo lee. Empresa no válida u obra de otra empresa,
        422 con motivo; una lectura que falla, 502."""
        if not empresa_valida(p.empresa):
            logger.warning("propuesta rechazada: empresa %r", p.empresa)
            return JSONResponse(status_code=422, content={
                "ok": False,
                "error": f"empresa no válida: {p.empresa!r}"})
        try:
            r = pipeline.proponer(
                empresa=p.empresa,
                obra=ObraEntrada(ide=p.obra.ide, codigo=p.obra.codigo,
                                 nombre=p.obra.nombre),
                ano=p.ano, mes=p.mes,
                lineas=[l.model_dump() for l in p.lineas])
        except Exception as exc:
            logger.exception("propuesta de partidas fallo")
            return JSONResponse(status_code=502,
                                content={"ok": False, "error": str(exc)})
        if not r["ok"]:
            logger.warning("propuesta rechazada: %s", r["error"])
            return JSONResponse(status_code=422, content=r)
        return r

    @app.post("/api/partidas/propuesta-lote")
    def propuesta_lote(p: PropuestaLoteIn):
        """F-055 (R34, R24, R25): síncrona, en el threadpool. Mismo periodo
        o 422; por petición `{ok: true, propuestas}` o `{ok: false,
        error}` (empresa no válida, obra de otra empresa o no encontrada);
        una lectura compartida que falla, 502."""
        if len({(x.ano, x.mes) for x in p.peticiones}) > 1:
            logger.warning("propuesta en lote rechazada: varios periodos")
            return JSONResponse(status_code=422, content={
                "ok": False,
                "error": "todas las peticiones tienen que ser del mismo "
                         "año y mes"})
        validas = [x for x in p.peticiones if empresa_valida(x.empresa)]
        try:
            resultados = iter(RegistroLote(
                cliente=cliente, settings=settings).proponer([
                    {"empresa": x.empresa,
                     "obra": ObraEntrada(ide=x.obra.ide, codigo=x.obra.codigo,
                                         nombre=x.obra.nombre),
                     "ano": x.ano, "mes": x.mes,
                     "lineas": [l.model_dump() for l in x.lineas]}
                    for x in validas]))
        except Exception as exc:                # noqa: BLE001
            logger.exception("propuesta en lote fallo")
            return JSONResponse(status_code=502,
                                content={"ok": False, "error": str(exc)})
        obras = []
        for x in p.peticiones:
            if not empresa_valida(x.empresa):
                obras.append({"ok": False,
                              "error": f"empresa no válida: {x.empresa!r}"})
                continue
            r = next(resultados)
            if isinstance(r, Exception):
                r = {"ok": False, "error": str(r)}
            if not r["ok"]:
                logger.warning("propuesta en lote: una obra falla: %s",
                               r["error"])
            obras.append(r)
        return {"ok": True, "obras": obras}

    @app.post("/api/var/universo")
    async def universo_de_var(p: UniversoVarIn):
        if not empresa_valida(p.empresa):
            logger.warning("universo VAR rechazado: empresa %r", p.empresa)
            return JSONResponse(status_code=422, content={
                "ok": False,
                "error": f"empresa no válida: {p.empresa!r}"})
        try:
            return {"ok": True, **universo_var.calcular(p.empresa)}
        except Exception as exc:
            logger.exception("universo VAR fallo")
            return JSONResponse(status_code=502,
                                content={"ok": False, "error": str(exc)})

    return app
