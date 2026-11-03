# tests/test_f054_partida_var.py
"""F-054 · T26 (R47; D21, «si» del 2026-11-03): la api pone en la línea VAR
del registro el `partida_cod` sacado del `cod` de la entrada, para que el
transfer nombre la partida por su código en los motivos del preflight.

- `partida_de_entrada(cod, obra_cod)`, pura, inversa de `codigo_entrada`:
  `VAR-29` con obra `VAR` → `29`; `None` si el `cod` no empieza por
  `<obra>-`, queda vacío o falta el código de la obra.
- La línea VAR lleva `partida_cod` solo si no es `None` (sin la clave, el
  transfer nombra el `ide`); nunca la elegida de la fila (F-050 R19). Las
  líneas normales y de postventa, idénticas a hoy.

Sin red ni BBDD: los dobles de `test_f039_registro_var.py`.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from domain.obras import codigo_entrada, partida_de_entrada

from tests.test_f039_registro_var import (
    O678,
    VAR_29,
    VAR_IDE,
    _fila,
    _obra,
    _payloads,
)


@pytest.mark.parametrize("cod, obra_cod, esperado", [
    ("VAR-29", "VAR", "29"),
    ("VAR-29.1", "VAR", "29.1"),
    (" VAR-29 ", " VAR ", "29"),
    ("VAR-CI-1", "VAR", "CI-1"),
    ("VARIOS-29", "VAR", None),
    ("X-29", "VAR", None),
    ("VAR29", "VAR", None),
    ("VAR-", "VAR", None),
    ("VAR- ", "VAR", None),
    ("", "VAR", None),
    (None, "VAR", None),
    ("VAR-29", None, None),
    ("VAR-29", "", None),
    ("VAR-29", "  ", None),
    ("-29", "", None),
])
def test_f054_r47_partida_de_entrada(cod, obra_cod, esperado):
    assert partida_de_entrada(cod, obra_cod) == esperado


@pytest.mark.parametrize("obra_cod, partida_cod", [
    ("VAR", "29"), ("VAR", "29.1"), ("OBRAS", "CI-1")])
def test_f054_r47_partida_de_entrada_es_la_inversa_de_codigo_entrada(
        obra_cod, partida_cod):
    assert partida_de_entrada(codigo_entrada(obra_cod, partida_cod),
                              obra_cod) == partida_cod


def _linea(obra: SimpleNamespace, **asignacion) -> dict:
    asig, trab, o = _fila(1, 10, obra)
    for k, v in asignacion.items():
        setattr(asig, k, v)
    return _payloads([(asig, trab, o)])[0]["lineas"][0]


def test_f054_r47_la_linea_var_lleva_el_codigo_de_su_partida():
    ln = _linea(VAR_29)
    assert (ln["var_paride"], ln["partida_cod"]) == (417055, "29")
    assert "paride" not in ln


@pytest.mark.parametrize("cod, registro_cod", [
    ("OTRA-29", "VAR"), ("VAR-", "VAR"), ("VAR-29", None)])
def test_f054_r47_sin_codigo_de_partida_la_linea_va_sin_la_clave(
        cod, registro_cod):
    entrada = _obra(-417055, cod, "NAVE",
                    registro=(VAR_IDE, registro_cod, 417055))
    ln = _linea(entrada)
    assert ln["var_paride"] == 417055
    assert "partida_cod" not in ln and "paride" not in ln


def test_f054_r47_nunca_la_elegida_de_la_fila():
    ln = _linea(VAR_29, partida_ide=80003, partida_cod="CI.1.9")
    assert ln["partida_cod"] == "29" and "paride" not in ln


@pytest.mark.parametrize("pv", [False, True])
def test_f054_r47_normales_y_postventa_como_hoy(pv):
    asig, trab, o = _fila(1, 10, O678, pv=pv)
    [ln] = _payloads([(asig, trab, o)])[0]["lineas"]
    assert ln == {"registro_id": 1, "ano": 2026, "mes": 8, "porcentaje": 0.4,
                  "recurso_ide": 10, "dni": None, "nombre": "T10",
                  "categoria": "Encargado", "es_postventa": pv, "empresa": 1}
    asig.partida_ide, asig.partida_cod = 2105, "CI.1.5"
    [ln] = _payloads([(asig, trab, o)])[0]["lineas"]
    assert (ln["paride"], ln["partida_cod"]) == (2105, "CI.1.5")
    assert "var_paride" not in ln
