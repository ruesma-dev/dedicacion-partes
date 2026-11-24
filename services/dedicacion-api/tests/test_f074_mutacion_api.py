# tests/test_f074_mutacion_api.py
"""F-074 · Tests que matan supervivientes de la campaña de mutación
`critico` (`progress/mutacion_F-074.md`), reproducidos en serie antes de
escribirlos (C4 bis).

- `estado_partida.py:33`: `Marcas` es inmutable: la foto de la cola que
  comparten cuadrante y rutas no se retoca por el camino.
- `schemas.py:154`: en `SubfilaOut`, `propuesta_no_encontrada` solo se
  excluye si es None (como `copiado`, F-069): un False también es valor.
"""
from __future__ import annotations

import dataclasses

import pytest

from application.estado_partida import Marcas
from interface_adapters.api.schemas import SubfilaOut


def test_f074_mut_las_marcas_son_inmutables():
    m = Marcas()
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.pendientes = frozenset({(1, 2, False)})  # type: ignore[misc]


def _subfila(**kw) -> dict:
    return SubfilaOut(vinculado_ide=10, tipo="TF", tipo_res=None, cod=None,
                      partida_ide=None, partida_cod=None, partida_res=None,
                      partida_fija=False, **kw).model_dump()


def test_f074_mut_subfila_solo_excluye_none():
    assert "propuesta_no_encontrada" not in _subfila()
    assert _subfila(propuesta_no_encontrada=False)[
        "propuesta_no_encontrada"] is False
    assert _subfila(propuesta_no_encontrada=True)[
        "propuesta_no_encontrada"] is True
