# domain/vigencia.py
"""Vigencia de un trabajador por mes (F-026, D3).

Un recurso dado de baja en el mes M sigue visible y registrable en M: «si el
recurso se ha dado de baja en el mes, debe salir todavía accesible»
(decisión del humano del 2026-10-02). Las fechas son las de Sigrid, enteros
`AAAAMMDD` con 0 = sin fecha (`azure-apps/sigrid_api.md`).

Única regla de vigencia: la usan el repositorio (cuadrante, resumen, copia y
export del mes) y el registro (qué líneas se mandan al transfer). Ver
`docs/ARCHITECTURE.md#regla-recurso`.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date


def inicio_de_mes(anio: int, mes: int) -> int:
    """Primer día del mes como entero `AAAAMM01`."""
    return int(anio) * 10000 + int(mes) * 100 + 1


def vigente_en(activo: bool, fecha_baja: int | None, anio: int,
               mes: int) -> bool:
    """¿El trabajador cuenta en el mes `anio`/`mes`?

    Sí si está activo (el sync lo sigue trayendo) y no tiene fecha de baja o
    la tiene el primer día del mes o después (R14).
    """
    return bool(activo) and (
        not fecha_baja or fecha_baja >= inicio_de_mes(anio, mes)
    )


def inicio_ventana_baja(abiertos: Iterable[tuple[int, int]], hoy: date) -> int:
    """Primer día desde el que el sync conserva los recursos con baja (R12).

    Es el más antiguo entre el mes anterior al de `hoy` (el que se captura a
    primeros de mes aunque aún no esté abierto) y cada periodo abierto
    `(anio, mes)`: así cada mes donde se captura o se registra tiene a sus
    trabajadores con baja en ese mes.
    """
    if hoy.month == 1:
        anterior = inicio_de_mes(hoy.year - 1, 12)
    else:
        anterior = inicio_de_mes(hoy.year, hoy.month - 1)
    return min([anterior, *(inicio_de_mes(a, m) for a, m in abiertos)])
