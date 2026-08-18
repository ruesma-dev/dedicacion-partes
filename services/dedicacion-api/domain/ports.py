# domain/ports.py
"""Puertos de la arquitectura hexagonal.

Los casos de uso dependen de estos Protocols; las implementaciones viven
en infrastructure/ (PostgreSQL, sigrid-api, openpyxl).
"""
from __future__ import annotations

from typing import Any, Protocol

from domain.models import (
    CuadranteTrabajador,
    Linea,
    Obra,
    Periodo,
    ResultadoSyncMaestro,
    TipoEvento,
    Trabajador,
)


class SigridGateway(Protocol):
    """Acceso de solo lectura a Sigrid vía sigrid-api."""

    def leer(self, sql: str) -> list[dict[str, Any]]:
        """Ejecuta la consulta y devuelve filas como dicts columna→valor."""
        ...


class TrabajadorRepository(Protocol):
    def sincronizar(self, filas: list[dict[str, Any]]) -> ResultadoSyncMaestro: ...

    def listar_para_periodo(self, periodo_id: int) -> list[Trabajador]:
        """Activos + inactivos que tengan líneas en el periodo."""
        ...

    def obtener(self, ide: int) -> Trabajador | None: ...


class ObraRepository(Protocol):
    def sincronizar(self, filas: list[dict[str, Any]]) -> ResultadoSyncMaestro: ...

    def listar_para_periodo(self, periodo_id: int) -> list[Obra]:
        """Activas + inactivas usadas en el periodo."""
        ...

    def existen(self, ides: set[int]) -> set[int]:
        """Subconjunto de `ides` que existen en el maestro."""
        ...


class PeriodoRepository(Protocol):
    def listar(self) -> list[Periodo]: ...

    def obtener(self, anio: int, mes: int) -> tuple[int, Periodo] | None:
        """Devuelve (id interno, Periodo) o None."""
        ...

    def crear(self, anio: int, mes: int) -> tuple[int, Periodo]: ...

    def cambiar_estado(self, anio: int, mes: int, estado: str) -> Periodo: ...

    def anterior_con_datos(self, anio: int, mes: int) -> tuple[int, Periodo] | None:
        """Último periodo anterior a (anio, mes) con alguna asignación."""
        ...


class AsignacionRepository(Protocol):
    def lineas_de_trabajador(self, periodo_id: int, trabajador_ide: int) -> list[Linea]: ...

    def lineas_del_periodo(self, periodo_id: int) -> dict[int, list[Linea]]:
        """Mapa trabajador_ide → líneas (con datos de obra resueltos)."""
        ...

    def reemplazar(
        self,
        periodo_id: int,
        trabajador_ide: int,
        lineas: list[Linea],
        usuario: str,
    ) -> None:
        """Sustituye en bloque las líneas del trabajador (transaccional)."""
        ...


class EventoRepository(Protocol):
    def registrar(
        self,
        periodo_id: int,
        trabajador_ide: int,
        tipo: TipoEvento,
        usuario: str,
        antes: list[dict[str, Any]],
        despues: list[dict[str, Any]],
    ) -> None: ...

    def ultimo_pendiente(
        self, periodo_id: int, trabajador_ide: int
    ) -> tuple[int, list[dict[str, Any]]] | None:
        """(id evento, snapshot_antes) del último evento no deshecho."""
        ...

    def marcar_deshecho(self, evento_id: int) -> None: ...

    def trabajadores_con_pendientes(self, periodo_id: int) -> set[int]: ...


class UnitOfWork(Protocol):
    """Frontera transaccional que agrupa los repositorios."""

    trabajadores: TrabajadorRepository
    obras: ObraRepository
    periodos: PeriodoRepository
    asignaciones: AsignacionRepository
    eventos: EventoRepository

    def __enter__(self) -> "UnitOfWork": ...

    def __exit__(self, *exc: object) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class ExcelExporter(Protocol):
    def exportar(
        self,
        periodo: Periodo,
        filas: list[CuadranteTrabajador],
    ) -> bytes: ...
