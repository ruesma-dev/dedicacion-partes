# tests/test_f026_vigencia.py
"""Tests offline de F-026: identidad por recurso y vigencia por mes.

Trazabilidad con `specs/F-026-recursos-sin-ficha-empleado/requirements.md`:
R7-R9 (clave = `res.ide`, `fecha_baja` en el ORM, desactivar lo que no
llega), R12 (ventana de bajas), R14 (vigente en el mes) y R15 (cuadrante,
resumen y copia por mes).

Nada abre un socket ni una conexión: el repositorio trabaja contra sesiones
dobles (patrón de F-023/F-024) y el DDL se compila con el dialecto
PostgreSQL sin motor. Los módulos de F-026 se importan dentro de los tests
para que cada tarea de `tasks.md` se verifique con su `-k`.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import pytest


def _vigencia() -> Any:
    from domain import vigencia

    return vigencia


# --- R14: vigente en el mes -------------------------------------------------


def test_f026_r14_inicio_de_mes_es_aaaamm01() -> None:
    v = _vigencia()
    assert v.inicio_de_mes(2026, 10) == 20261001
    assert v.inicio_de_mes(2027, 1) == 20270101
    assert v.inicio_de_mes(2026, 12) == 20261201


@pytest.mark.parametrize(("activo", "fecha_baja", "esperado"), [
    (True, None, True),          # sin baja
    (True, 0, True),             # 0 de Sigrid = sin baja
    (True, 20261001, True),      # baja el día 1 del mes: sigue ese mes (D3)
    (True, 20261031, True),      # baja el último día del mes
    (True, 20261115, True),      # baja posterior
    (True, 20260930, False),     # baja el último día del mes anterior
    (True, 20260901, False),     # baja del mes anterior
    (False, None, False),        # inactivo: no vigente, sin mirar la baja
    (False, 20261015, False),
])
def test_f026_r14_vigente_en_octubre(activo: bool, fecha_baja: int | None,
                                     esperado: bool) -> None:
    assert _vigencia().vigente_en(activo, fecha_baja, 2026, 10) is esperado


# --- R12: ventana de bajas --------------------------------------------------


def test_f026_r12_ventana_sin_abiertos_es_el_mes_anterior_a_hoy() -> None:
    assert _vigencia().inicio_ventana_baja([], date(2026, 10, 2)) == 20260901


def test_f026_r12_ventana_en_enero_es_diciembre_del_anio_anterior() -> None:
    assert _vigencia().inicio_ventana_baja([], date(2027, 1, 31)) == 20261201


def test_f026_r12_el_periodo_abierto_mas_antiguo_gana() -> None:
    abiertos = [(2026, 10), (2026, 6), (2026, 8)]
    assert _vigencia().inicio_ventana_baja(
        abiertos, date(2026, 10, 2)) == 20260601


def test_f026_r12_un_abierto_posterior_no_mueve_la_ventana() -> None:
    abiertos = [(2026, 10), (2026, 11)]
    assert _vigencia().inicio_ventana_baja(
        abiertos, date(2026, 10, 2)) == 20260901


def test_f026_r12_acepta_cualquier_iterable() -> None:
    abiertos = iter([(2025, 12)])
    assert _vigencia().inicio_ventana_baja(
        abiertos, date(2026, 10, 2)) == 20251201
