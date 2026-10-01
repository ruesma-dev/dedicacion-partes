# tests/test_f024_visibilidad.py
"""F-024 · Regla de visibilidad por empresa (R8, R10, R11).

La regla vive en UNA función de dominio (`domain/empresas.py`) que usan el
cuadrante y el registro: aquí se prueba con tablas de casos, sin red ni BBDD.
La regla de negocio está en `docs/ARCHITECTURE.md#regla-empresa`.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from decimal import Decimal

import pytest

from domain.empresas import linea_de_otra_empresa, visible_en_empresa
from domain.models import FiltroEmpresa, Linea

#: Empresa por defecto de los tests (Construcciones Ruesma).
DEF = 1


def _f(empresa: int) -> FiltroEmpresa:
    return FiltroEmpresa(empresa=empresa, por_defecto=DEF)


# ------------------------------- R8 ----------------------------------- #
@pytest.mark.parametrize("empresa_trab, obras, elegida, visible", [
    # Con empresa: solo en la suya, tenga las líneas donde las tenga.
    (1, [], 1, True),
    (1, [], 28, False),
    (28, [], 28, True),
    (28, [], 1, False),
    (1, [28, 28], 28, False),
    (1, [28], 1, True),
    (18, [None], 1, False),
])
def test_f024_r8_trabajador_con_empresa_solo_en_la_suya(
        empresa_trab, obras, elegida, visible):
    assert visible_en_empresa(empresa_trab, obras, _f(elegida)) is visible


@pytest.mark.parametrize("obras, elegida, visible", [
    # NULL con obras de UNA empresa: solo en esa.
    ([28], 28, True),
    ([28], 1, False),
    ([28, 28], 28, True),
    # NULL con obras de DOS empresas: en las dos.
    ([1, 28], 1, True),
    ([1, 28], 28, True),
    ([1, 28], 18, False),
    # NULL con obras conocidas y alguna NULL: cuentan solo las conocidas.
    ([None, 28], 28, True),
    ([None, 28], 1, False),
])
def test_f024_r8_trabajador_null_donde_tiene_carga(obras, elegida, visible):
    assert visible_en_empresa(None, obras, _f(elegida)) is visible


@pytest.mark.parametrize("obras", [[], [None], [None, None]],
                         ids=["sin_lineas", "una_obra_null", "dos_obras_null"])
@pytest.mark.parametrize("elegida, visible", [(1, True), (28, False),
                                              (18, False)])
def test_f024_r8_trabajador_null_sin_obras_con_empresa_en_la_por_defecto(
        obras, elegida, visible):
    """Sin líneas, o con líneas solo en obras sin empresa: solo en la por
    defecto."""
    assert visible_en_empresa(None, obras, _f(elegida)) is visible


def test_f024_r8_por_defecto_sale_del_filtro_no_de_un_literal():
    """La por defecto es la del filtro (EMPRESA_IMPUTACION), no un 1 fijo."""
    filtro = FiltroEmpresa(empresa=28, por_defecto=28)
    assert visible_en_empresa(None, [], filtro) is True
    assert visible_en_empresa(None, [], FiltroEmpresa(1, 28)) is False


def test_f024_r8_acepta_cualquier_iterable_una_sola_vez():
    """La función recorre las empresas de las obras una sola vez: vale un
    generador."""
    gen = (e for e in [None, 28])
    assert visible_en_empresa(None, gen, _f(28)) is True


# ------------------------------- R11 ---------------------------------- #
@pytest.mark.parametrize("obra_empresa, empresa, otra", [
    (None, 1, False),
    (1, 1, False),
    (28, 1, True),
    (1, 28, True),
    (28, 28, False),
])
def test_f024_r11_linea_de_otra_empresa(obra_empresa, empresa, otra):
    assert linea_de_otra_empresa(obra_empresa, empresa) is otra


def test_f024_r11_linea_lleva_obra_empresa_opcional():
    campos = {f.name: f for f in fields(Linea)}
    assert campos["obra_empresa"].default is None
    ln = Linea(obra_ide=1, es_postventa=False, porcentaje=Decimal(10),
               obra_empresa=28)
    assert ln.obra_empresa == 28


def test_f024_r8_filtro_empresa_inmutable():
    filtro = _f(1)
    assert (filtro.empresa, filtro.por_defecto) == (1, DEF)
    with pytest.raises(FrozenInstanceError):
        filtro.empresa = 28  # type: ignore[misc]


# ------------------------------- R10 ---------------------------------- #
def test_f024_r10_la_regla_no_quita_lineas():
    """R10 · La visibilidad decide la FILA, no sus líneas: un trabajador de
    la 1 con una línea en una obra de la 28 sigue visible en la 1 y esa
    línea se marca (no se filtra)."""
    lineas = [Linea(1, False, Decimal(60), obra_empresa=1),
              Linea(2, False, Decimal(40), obra_empresa=28)]
    assert visible_en_empresa(1, [ln.obra_empresa for ln in lineas], _f(1))
    assert [linea_de_otra_empresa(ln.obra_empresa, 1) for ln in lineas] == [
        False, True]
