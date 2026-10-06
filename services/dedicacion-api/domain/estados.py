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

import dataclasses
from decimal import Decimal

from domain.models import (
    Completado,
    CuadranteTrabajador,
    EstadoTrabajador,
    Linea,
    ResumenPeriodo,
)

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


def completar_hasta_100(
    lineas: list[Linea], obra_ide: int, es_postventa: bool
) -> Completado | None:
    """Pone lo que le falta al trabajador hasta el 100 % en el destino
    (obra + modo) (F-029, docs/ARCHITECTURE.md#regla-completar).

    `None` si ya está en OK o en EXCESO según `calcular_estado` (la misma
    épsilon: no hay un segundo criterio de «al 100 %»). Lo que falta es
    100 menos el total de TODAS sus líneas, a centésimas (D5). Si ya tiene
    línea con la clave (obra, `es_postventa`), se suma a ella; si no, va
    una línea nueva al final. Las demás líneas salen idénticas.

    No mira empresa, vigencia ni si la obra se ofrece: eso es del caso de
    uso `CompletarHasta100`.
    """
    total = sum((ln.porcentaje for ln in lineas), Decimal("0"))
    estado = calcular_estado(total, len(lineas))
    if estado in (EstadoTrabajador.OK, EstadoTrabajador.EXCESO):
        return None
    falta = (_CIEN - total).quantize(Decimal("0.01"))
    clave = (obra_ide, es_postventa)
    resultado: list[Linea] = []
    sumada = False
    for ln in lineas:
        if ln.clave() == clave:
            resultado.append(
                dataclasses.replace(ln, porcentaje=ln.porcentaje + falta)
            )
            sumada = True
        else:
            resultado.append(ln)
    if not sumada:
        resultado.append(
            Linea(obra_ide=obra_ide, es_postventa=es_postventa, porcentaje=falta)
        )
    return Completado(lineas=resultado, anadido=falta)


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
