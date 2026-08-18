# application/sync_pipeline.py
"""Pipeline de sincronización de maestros (empleados y obras).

Patrón Pipeline + Steps con objeto de contexto, como en el resto de
microservicios: cada paso recibe/enriquece el SyncContext y el pipeline
los ejecuta en orden dentro de una única transacción.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Protocol

from application.filtros_maestros import depurar_empleados, depurar_obras
from domain.models import ResultadoSync, ResultadoSyncMaestro
from domain.ports import SigridGateway, UnitOfWork

logger = logging.getLogger(__name__)


@dataclass
class SyncContext:
    filas_empleados: list[dict[str, Any]] = field(default_factory=list)
    filas_obras: list[dict[str, Any]] = field(default_factory=list)
    resultado_empleados: ResultadoSyncMaestro | None = None
    resultado_obras: ResultadoSyncMaestro | None = None


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
    ) -> None:
        self._sigrid = sigrid
        self._sql = sql
        self._categorias = categorias_incluidas or []
        self._filtro = filtro_activo and bool(self._categorias)
        self._exigir_mes = bool(exigir_codigo_mes)

    def ejecutar(self, ctx: SyncContext, uow: UnitOfWork) -> None:
        brutas = self._sigrid.leer(self._sql)
        _validar_columnas(brutas, {"ide", "nombre"}, "sync.empleados.sql")
        depurado = depurar_empleados(
            brutas, self._categorias, self._filtro,
            exigir_codigo_mes=self._exigir_mes,
        )
        logger.info(
            "sync empleados: %d brutos, %d duplicados de recurso, "
            "%d duplicados de persona, %d sin código de hora mensual, "
            "%d excluidos por categoría, %d netos",
            depurado.brutos,
            depurado.duplicados_recurso,
            depurado.duplicados_persona,
            depurado.excluidos_sin_codigo_mes,
            depurado.excluidos_filtro,
            len(depurado.filas),
        )
        ctx.filas_empleados = depurado.filas


class FetchObrasStep:
    nombre = "fetch_obras"

    def __init__(
        self,
        sigrid: SigridGateway,
        sql: str,
        estados_excluidos: list[str] | None = None,
        filtro_activo: bool = True,
    ) -> None:
        self._sigrid = sigrid
        self._sql = sql
        self._estados = estados_excluidos or []
        self._filtro = filtro_activo and bool(self._estados)

    def ejecutar(self, ctx: SyncContext, uow: UnitOfWork) -> None:
        brutas = self._sigrid.leer(self._sql)
        _validar_columnas(brutas, {"ide", "cod"}, "sync.obras.sql")
        depurado = depurar_obras(brutas, self._estados, self._filtro)
        logger.info(
            "sync obras: %d brutas, %d excluidas por estado, %d netas",
            depurado.brutos,
            depurado.excluidos_filtro,
            len(depurado.filas),
        )
        ctx.filas_obras = depurado.filas


class UpsertTrabajadoresStep:
    nombre = "upsert_trabajadores"

    def ejecutar(self, ctx: SyncContext, uow: UnitOfWork) -> None:
        ctx.resultado_empleados = uow.trabajadores.sincronizar(ctx.filas_empleados)


class UpsertObrasStep:
    nombre = "upsert_obras"

    def ejecutar(self, ctx: SyncContext, uow: UnitOfWork) -> None:
        ctx.resultado_obras = uow.obras.sincronizar(ctx.filas_obras)


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
        logger.info(
            "sync completado en %.2fs: empleados=%s obras=%s",
            duracion,
            ctx.resultado_empleados,
            ctx.resultado_obras,
        )
        return ResultadoSync(
            empleados=ctx.resultado_empleados,
            obras=ctx.resultado_obras,
            duracion_s=duracion,
        )


def _validar_columnas(
    filas: list[dict[str, Any]], requeridas: set[str], origen: str
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
