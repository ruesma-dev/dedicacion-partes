# application/sync_pipeline.py
"""Pipeline de sincronización de maestros (empleados, obras y empresas).

Patrón Pipeline + Steps con objeto de contexto, como en el resto de
microservicios: cada paso recibe/enriquece el SyncContext y el pipeline
los ejecuta en orden dentro de una única transacción.
"""
from __future__ import annotations

import logging
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Protocol

from application.filtros_maestros import (
    CRITERIO_VACIO,
    CriterioActivoRecurso,
    ResultadoDepuracion,
    depurar_empleados,
    depurar_obras,
    descartar_por_codigo,
    entradas_var,
)
from domain.models import (
    EstadoPeriodo,
    Periodo,
    ResultadoSync,
    ResultadoSyncMaestro,
    ResultadoUniverso,
    ResultadoUniversoVar,
)
from domain.normalizacion import entero_o_none, texto_o_none
from domain.ports import (
    SigridGateway,
    UniversoPostventaGateway,
    UniversosGateway,
    UnitOfWork,
)
from domain.vigencia import inicio_ventana_baja

logger = logging.getLogger(__name__)

#: Columnas sin las que no se sincroniza (F-023 R6). Las comparte el preview
#: (`use_cases.PreviewSync`) para que los dos exijan exactamente lo mismo.
COLUMNAS_EMPLEADOS = frozenset({"ide", "nombre", "empresa"})
COLUMNAS_OBRAS = frozenset({"ide", "cod", "empresa"})
#: Catálogo `auxemp` (F-032): sin número no hay con qué casar `con.emp`, y
#: sin nombre la tabla no sirve para lo que existe.
COLUMNAS_EMPRESAS = frozenset({"numemp", "nombre"})


@dataclass
class SyncContext:
    filas_empleados: list[dict[str, Any]] = field(default_factory=list)
    filas_obras: list[dict[str, Any]] = field(default_factory=list)
    filas_empresas: list[dict[str, Any]] = field(default_factory=list)
    resultado_empleados: ResultadoSyncMaestro | None = None
    resultado_obras: ResultadoSyncMaestro | None = None
    resultado_empresas: ResultadoSyncMaestro | None = None


def ventana_de_bajas(periodos: Iterable[Periodo], hoy: date) -> int:
    """Ventana de bajas (F-026 R12) con los periodos `ABIERTO` de la base.

    La comparten el step del sync y el preview, para que los dos depuren
    con la misma ventana.
    """
    abiertos = [p.clave for p in periodos if p.estado is EstadoPeriodo.ABIERTO]
    return inicio_ventana_baja(abiertos, hoy)


def pedir_universo(
    universo: UniversoPostventaGateway,
    filas: list[dict[str, Any]],
    empresa_obras: int,
) -> ResultadoUniverso:
    """Pide al transfer, UNA vez, el universo de postventa de la empresa de
    las obras (F-025, R12): todas las obras leídas de esa empresa, también
    las excluidas por estado; las de otras empresas no. Cada obra viaja con
    el `cod` y la `descripcion` que se guardarán, que son los que el
    preflight recibe después.

    La comparten el step del sync y el preview, para que los dos calculen
    el mismo universo.
    """
    obras = [
        {"ide": int(f["ide"]), "codigo": texto_o_none(f.get("cod")),
         "nombre": texto_o_none(f.get("descripcion")) or ""}
        for f in filas if entero_o_none(f.get("empresa")) == empresa_obras
    ]
    return universo.universo_postventa(empresa_obras, obras)


@dataclass(frozen=True)
class ObrasPreparadas:
    """Lo que el sync guarda de las obras y lo que el preview enseña (F-039):
    las filas depuradas (con las entradas VAR), los dos universos, las
    entradas VAR y las obras descartadas por código."""

    depurado: ResultadoDepuracion
    universo_pv: ResultadoUniverso
    universo_var: ResultadoUniversoVar
    entradas: list[dict[str, Any]]
    descartadas: list[dict[str, Any]]


def preparar_obras(
    brutas: list[dict[str, Any]],
    universo: UniversosGateway,
    empresa_obras: int,
    estados: list[str],
    filtro: bool,
    digitos: int,
) -> ObrasPreparadas:
    """Depura las obras leídas de Sigrid. UNA función para el step y el
    preview: lo que enseña el preview es lo que se guarda.

    1. Fuera las de código con `digitos`+ dígitos seguidos, antes de pedir
       ningún universo (docs/ARCHITECTURE.md#regla-seis-digitos).
    2. Universo de postventa con las que quedan (F-025) y universo VAR de la
       empresa de las obras, una petición cada uno (#regla-var).
    3. Marcas de F-025; la obra VAR no se ofrece como normal (D1) y cada
       partida VAR entra como fila propia (`entradas_var`).
    """
    quedan, descartadas = descartar_por_codigo(brutas, digitos)
    universo_pv = pedir_universo(universo, quedan, empresa_obras)
    universo_var = universo.universo_var(empresa_obras)
    no_normales = (frozenset({universo_var.obra_ide})
                   if universo_var.obra_ide is not None else frozenset())
    depurado = depurar_obras(quedan, estados, filtro, universo_pv.ides,
                             no_normales)
    depurado.brutos = len(brutas)
    entradas = entradas_var(universo_var)
    depurado.filas.extend(entradas)
    return ObrasPreparadas(depurado=depurado, universo_pv=universo_pv,
                           universo_var=universo_var, entradas=entradas,
                           descartadas=descartadas)


class SyncStep(Protocol):
    nombre: str

    def ejecutar(self, ctx: SyncContext, uow: UnitOfWork) -> None: ...


# ----------------------------------------------------------------------
# Pasos
# ----------------------------------------------------------------------
class FetchEmpleadosStep:
    nombre = "fetch_empleados"

    def __init__(
        self,
        sigrid: SigridGateway,
        sql: str,
        categorias_incluidas: list[str] | None = None,
        filtro_activo: bool = True,
        exigir_codigo_mes: bool = True,
        criterio: CriterioActivoRecurso = CRITERIO_VACIO,
        hoy: Callable[[], date] = date.today,
    ) -> None:
        self._sigrid = sigrid
        self._sql = sql
        self._categorias = categorias_incluidas or []
        self._filtro = filtro_activo and bool(self._categorias)
        self._exigir_mes = bool(exigir_codigo_mes)
        self._criterio = criterio
        # Reloj inyectable (F-026 R12): los tests fijan el día.
        self._hoy = hoy

    def ejecutar(self, ctx: SyncContext, uow: UnitOfWork) -> None:
        brutas = self._sigrid.leer(self._sql)
        _validar_columnas(brutas, COLUMNAS_EMPLEADOS, "sync.empleados.sql")
        baja_desde = ventana_de_bajas(uow.periodos.listar(), self._hoy())
        depurado = depurar_empleados(
            brutas, self._categorias, self._filtro,
            exigir_codigo_mes=self._exigir_mes,
            criterio=self._criterio,
            baja_desde=baja_desde,
        )
        logger.info(
            "sync empleados (ventana de bajas %d): %d brutos, "
            "%d por estado del recurso, "
            "%d sin código de hora mensual, %d excluidos por categoría, "
            "%d netos (%d con baja laboral, %d con fecha de baja, "
            "%d grupos de posible misma persona)",
            baja_desde,
            depurado.brutos,
            sum(depurado.excluidos_estado_recurso.values()),
            depurado.excluidos_sin_codigo_mes,
            depurado.excluidos_filtro,
            len(depurado.filas),
            depurado.con_baja_laboral,
            depurado.incluidos_con_baja,
            len(depurado.posible_misma_persona),
        )
        ctx.filas_empleados = depurado.filas


class FetchObrasStep:
    """Lee las obras y las prepara con `preparar_obras`: descarte por código
    (F-039), marcas `activa` y `admite_postventa` (F-025) y entradas VAR
    (F-039). Sin universo de postventa o VAR, el sync falla entero: el error
    sube antes de persistir nada."""

    nombre = "fetch_obras"

    def __init__(
        self,
        sigrid: SigridGateway,
        sql: str,
        estados_excluidos: list[str] | None = None,
        filtro_activo: bool = True,
        *,
        universo: UniversosGateway,
        empresa_obras: int,
        digitos_excluidos: int = 0,
    ) -> None:
        self._sigrid = sigrid
        self._sql = sql
        self._estados = estados_excluidos or []
        self._filtro = filtro_activo and bool(self._estados)
        self._universo = universo
        self._empresa_obras = empresa_obras
        self._digitos = digitos_excluidos

    def ejecutar(self, ctx: SyncContext, uow: UnitOfWork) -> None:
        brutas = self._sigrid.leer(self._sql)
        _validar_columnas(brutas, COLUMNAS_OBRAS, "sync.obras.sql")
        prep = preparar_obras(brutas, self._universo, self._empresa_obras,
                              self._estados, self._filtro, self._digitos)
        depurado = prep.depurado
        logger.info(
            "sync obras: %d brutas, %d excluidas por código, %d excluidas "
            "por estado, %d netas (%d admiten postventa, %d solo postventa; "
            "motivo: %s; %d entradas VAR; motivo VAR: %s)",
            depurado.brutos,
            len(prep.descartadas),
            depurado.excluidos_filtro,
            len(depurado.filas),
            depurado.admiten_postventa,
            depurado.solo_postventa,
            prep.universo_pv.motivo,
            len(prep.entradas),
            prep.universo_var.motivo,
        )
        ctx.filas_obras = depurado.filas


class FetchEmpresasStep:
    """Lee el catálogo `auxemp` de Sigrid (F-032). Sin depuración: entran
    también las de baja o desactivadas, que el selector enseña marcadas."""

    nombre = "fetch_empresas"

    def __init__(self, sigrid: SigridGateway, sql: str) -> None:
        self._sigrid = sigrid
        self._sql = sql

    def ejecutar(self, ctx: SyncContext, uow: UnitOfWork) -> None:
        filas = self._sigrid.leer(self._sql)
        _validar_columnas(filas, COLUMNAS_EMPRESAS, "sync.empresas.sql")
        logger.info("sync empresas: %d leídas", len(filas))
        ctx.filas_empresas = filas


class UpsertTrabajadoresStep:
    nombre = "upsert_trabajadores"

    def ejecutar(self, ctx: SyncContext, uow: UnitOfWork) -> None:
        ctx.resultado_empleados = uow.trabajadores.sincronizar(ctx.filas_empleados)


class UpsertObrasStep:
    nombre = "upsert_obras"

    def ejecutar(self, ctx: SyncContext, uow: UnitOfWork) -> None:
        ctx.resultado_obras = uow.obras.sincronizar(ctx.filas_obras)


class UpsertEmpresasStep:
    nombre = "upsert_empresas"

    def ejecutar(self, ctx: SyncContext, uow: UnitOfWork) -> None:
        ctx.resultado_empresas = uow.empresas.sincronizar(ctx.filas_empresas)


# ----------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------
class SyncMaestrosPipeline:
    def __init__(self, pasos: list[SyncStep]) -> None:
        self._pasos = pasos

    def ejecutar(self, uow: UnitOfWork) -> ResultadoSync:
        inicio = time.perf_counter()
        ctx = SyncContext()
        for paso in self._pasos:
            logger.info("sync: paso %s", paso.nombre)
            paso.ejecutar(ctx, uow)
        uow.commit()
        duracion = round(time.perf_counter() - inicio, 2)
        assert ctx.resultado_empleados and ctx.resultado_obras
        # La composición de pasos es del punto de entrada (deps.py): un
        # pipeline sin los de empresas devuelve sus contadores a cero.
        resultado = ResultadoSync(
            empleados=ctx.resultado_empleados,
            obras=ctx.resultado_obras,
            duracion_s=duracion,
            empresas=ctx.resultado_empresas or ResultadoSyncMaestro(),
        )
        logger.info(
            "sync completado en %.2fs: empleados=%s obras=%s empresas=%s",
            duracion,
            resultado.empleados,
            resultado.obras,
            resultado.empresas,
        )
        return resultado


def _validar_columnas(
    filas: list[dict[str, Any]], requeridas: frozenset[str], origen: str
) -> None:
    if not filas:
        return
    presentes = set(filas[0])
    faltan = requeridas - presentes
    if faltan:
        raise ValueError(
            f"La consulta {origen} no devuelve las columnas {sorted(faltan)}; "
            f"recibidas: {sorted(presentes)}"
        )
