# domain/models.py
"""Entidades de dominio del servicio de dedicación.

Sin dependencias de infraestructura: dataclasses puras que circulan entre
casos de uso, repositorios y adaptadores.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class EstadoPeriodo(str, Enum):
    ABIERTO = "ABIERTO"
    CERRADO = "CERRADO"


class EstadoTrabajador(str, Enum):
    OK = "OK"
    FALTA = "FALTA"
    EXCESO = "EXCESO"
    SIN_CARGA = "SIN_CARGA"


class TipoEvento(str, Enum):
    GUARDAR = "GUARDAR"
    COPIA = "COPIA"


@dataclass(frozen=True)
class Trabajador:
    ide: int
    cod: str | None
    nombre: str
    dni: str | None
    categoria: str | None
    activo: bool = True


@dataclass(frozen=True)
class Obra:
    ide: int
    cod: str
    descripcion: str
    estado_sigrid: str | None
    activa: bool = True


@dataclass(frozen=True)
class Periodo:
    anio: int
    mes: int
    estado: EstadoPeriodo = EstadoPeriodo.ABIERTO

    @property
    def clave(self) -> tuple[int, int]:
        return (self.anio, self.mes)


@dataclass(frozen=True)
class Linea:
    """Asignación de un trabajador a una obra dentro de un periodo."""

    obra_ide: int
    es_postventa: bool
    porcentaje: Decimal
    cod: str = ""
    descripcion: str = ""
    obra_activa: bool = True

    def clave(self) -> tuple[int, bool]:
        return (self.obra_ide, self.es_postventa)


@dataclass
class CuadranteTrabajador:
    """Fila del cuadrante: trabajador + sus líneas + estado calculado."""

    trabajador: Trabajador
    lineas: list[Linea] = field(default_factory=list)
    puede_deshacer: bool = False

    @property
    def total(self) -> Decimal:
        return sum((ln.porcentaje for ln in self.lineas), Decimal("0"))


@dataclass(frozen=True)
class ResumenPeriodo:
    total: int = 0
    ok: int = 0
    falta: int = 0
    exceso: int = 0
    sin_carga: int = 0


@dataclass(frozen=True)
class ResultadoSyncMaestro:
    recibidos: int = 0
    altas: int = 0
    actualizados: int = 0
    desactivados: int = 0


@dataclass(frozen=True)
class ResultadoSync:
    empleados: ResultadoSyncMaestro
    obras: ResultadoSyncMaestro
    duracion_s: float


@dataclass(frozen=True)
class ResultadoCopia:
    """Resultado de copiar asignaciones desde el periodo anterior."""

    periodo_origen: Periodo | None
    trabajadores_copiados: int = 0
    con_carga_previa: int = 0
    sin_datos_origen: int = 0
    lineas_omitidas_obra_inactiva: int = 0
