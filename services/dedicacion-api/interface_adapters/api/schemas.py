# interface_adapters/api/schemas.py
"""Schemas Pydantic v2 (contratos de entrada/salida de la API REST)."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from domain.estados import calcular_desviacion, calcular_estado
from domain.models import (
    CuadranteTrabajador,
    Obra,
    Periodo,
    ResultadoCopia,
    ResultadoSync,
    ResumenPeriodo,
)


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --------------------------- Entrada ----------------------------------
class LineaIn(_Base):
    obra_ide: int
    es_postventa: bool = False
    porcentaje: Decimal = Field(gt=0, le=100, max_digits=6, decimal_places=2)


class AsignacionesIn(_Base):
    lineas: list[LineaIn]


class PeriodoIn(_Base):
    anio: int = Field(ge=2020, le=2100)
    mes: int = Field(ge=1, le=12)


# --------------------------- Salida -----------------------------------
class LineaOut(_Base):
    obra_ide: int
    cod: str
    descripcion: str
    es_postventa: bool
    porcentaje: float
    obra_activa: bool


class TrabajadorOut(_Base):
    ide: int
    nombre: str
    categoria: str | None
    activo: bool
    lineas: list[LineaOut]
    total: float
    desviacion: float
    estado: str
    puede_deshacer: bool


class ObraOut(_Base):
    ide: int
    cod: str
    descripcion: str
    activa: bool
    estado_sigrid: str | None


class PeriodoOut(_Base):
    anio: int
    mes: int
    estado: str


class ResumenOut(_Base):
    total: int
    ok: int
    falta: int
    exceso: int
    sin_carga: int


class CuadranteOut(_Base):
    periodo: PeriodoOut
    obras: list[ObraOut]
    trabajadores: list[TrabajadorOut]
    resumen: ResumenOut


class FilaOut(_Base):
    trabajador: TrabajadorOut
    resumen: ResumenOut


class CopiaTrabajadorOut(FilaOut):
    periodo_origen: PeriodoOut | None
    lineas_omitidas_obra_inactiva: int


class CopiaPeriodoOut(_Base):
    periodo_origen: PeriodoOut | None
    trabajadores_copiados: int
    con_carga_previa: int
    sin_datos_origen: int
    lineas_omitidas_obra_inactiva: int


class SyncMaestroOut(_Base):
    recibidos: int
    altas: int
    actualizados: int
    desactivados: int


class SyncOut(_Base):
    empleados: SyncMaestroOut
    obras: SyncMaestroOut
    duracion_s: float


class PeriodoCreadoOut(PeriodoOut):
    creado: bool


class ErrorOut(_Base):
    error: str


# --------------------------- Mapeos -----------------------------------
def a_periodo_out(periodo: Periodo) -> PeriodoOut:
    return PeriodoOut(anio=periodo.anio, mes=periodo.mes, estado=periodo.estado.value)


def a_obra_out(obra: Obra) -> ObraOut:
    return ObraOut(
        ide=obra.ide,
        cod=obra.cod,
        descripcion=obra.descripcion,
        activa=obra.activa,
        estado_sigrid=obra.estado_sigrid,
    )


def a_trabajador_out(fila: CuadranteTrabajador) -> TrabajadorOut:
    total = fila.total
    estado = calcular_estado(total, len(fila.lineas))
    desviacion = calcular_desviacion(total, len(fila.lineas))
    return TrabajadorOut(
        ide=fila.trabajador.ide,
        nombre=fila.trabajador.nombre,
        categoria=fila.trabajador.categoria,
        activo=fila.trabajador.activo,
        lineas=[
            LineaOut(
                obra_ide=ln.obra_ide,
                cod=ln.cod,
                descripcion=ln.descripcion,
                es_postventa=ln.es_postventa,
                porcentaje=float(ln.porcentaje),
                obra_activa=ln.obra_activa,
            )
            for ln in fila.lineas
        ],
        total=float(total),
        desviacion=float(desviacion),
        estado=estado.value,
        puede_deshacer=fila.puede_deshacer,
    )


def a_resumen_out(resumen: ResumenPeriodo) -> ResumenOut:
    return ResumenOut(
        total=resumen.total,
        ok=resumen.ok,
        falta=resumen.falta,
        exceso=resumen.exceso,
        sin_carga=resumen.sin_carga,
    )


def a_sync_out(resultado: ResultadoSync) -> SyncOut:
    return SyncOut(
        empleados=SyncMaestroOut(**resultado.empleados.__dict__),
        obras=SyncMaestroOut(**resultado.obras.__dict__),
        duracion_s=resultado.duracion_s,
    )


def a_copia_periodo_out(resultado: ResultadoCopia) -> CopiaPeriodoOut:
    return CopiaPeriodoOut(
        periodo_origen=(
            a_periodo_out(resultado.periodo_origen)
            if resultado.periodo_origen
            else None
        ),
        trabajadores_copiados=resultado.trabajadores_copiados,
        con_carga_previa=resultado.con_carga_previa,
        sin_datos_origen=resultado.sin_datos_origen,
        lineas_omitidas_obra_inactiva=resultado.lineas_omitidas_obra_inactiva,
    )


def lineas_a_dicts(payload: AsignacionesIn) -> list[dict[str, Any]]:
    return [
        {
            "obra_ide": ln.obra_ide,
            "es_postventa": ln.es_postventa,
            "porcentaje": str(ln.porcentaje),
        }
        for ln in payload.lineas
    ]
