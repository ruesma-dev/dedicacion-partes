# domain/estados.py
"""Regla de control de la plantilla de dedicación.

Replica los estados de la hoja 03_Carga del Excel:
  - SIN_CARGA : sin asignaciones.
  - OK        : total = 100 %.
  - FALTA     : total < 100 %  (desviación negativa).
  - EXCESO    : total > 100 %  (desviación positiva).

Los pares incompletos y duplicados del Excel no pueden darse aquí: el
modelo de datos (constraint único obra+postventa por trabajador y
porcentaje obligatorio) los hace imposibles por diseño.
"""
from __future__ import annotations

from decimal import Decimal

from domain.models import CuadranteTrabajador, EstadoTrabajador, ResumenPeriodo

_CIEN = Decimal("100")
_EPSILON = Decimal("0.005")


def calcular_estado(total: Decimal, num_lineas: int) -> EstadoTrabajador:
    if num_lineas == 0:
        return EstadoTrabajador.SIN_CARGA
    if abs(total - _CIEN) <= _EPSILON:
        return EstadoTrabajador.OK
    if total < _CIEN:
        return EstadoTrabajador.FALTA
    return EstadoTrabajador.EXCESO


def calcular_desviacion(total: Decimal, num_lineas: int) -> Decimal:
    if num_lineas == 0:
        return Decimal("0")
    return (total - _CIEN).quantize(Decimal("0.01"))


def resumir(filas: list[CuadranteTrabajador]) -> ResumenPeriodo:
    contadores = {estado: 0 for estado in EstadoTrabajador}
    visibles = 0
    for fila in filas:
        # Las bajas sin carga no cuentan (tampoco se muestran en el front).
        if not fila.trabajador.activo and not fila.lineas:
            continue
        visibles += 1
        contadores[calcular_estado(fila.total, len(fila.lineas))] += 1
    return ResumenPeriodo(
        total=visibles,
        ok=contadores[EstadoTrabajador.OK],
        falta=contadores[EstadoTrabajador.FALTA],
        exceso=contadores[EstadoTrabajador.EXCESO],
        sin_carga=contadores[EstadoTrabajador.SIN_CARGA],
    )
