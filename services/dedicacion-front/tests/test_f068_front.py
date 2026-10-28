# tests/test_f068_front.py
"""F-068 · T11: el rótulo del método nuevo de la subfila (R20).

El front solo pinta: `rotuloOrigen` rotula `capitulo_ci4` («capítulo CI.4
en empate») en la subfila del cuadrante y en el modal de registro;
`parte_anterior`, `ci_tipo` y `auto_*` siguen con los rótulos que ya tiene.
Código REAL de `app.js` en `node` con los arneses de F-044 y F-050. Sin
`node`, se saltan con su motivo; el reviewer los exige `passed`. Sin red.
"""
from __future__ import annotations

import pytest

from tests.test_f044_vinculados_front import (
    LINEA,
    TEL,
    _accion_reg,
    _celdas,
    _filas_tabla,
    _modal_vin,
    _obra_reg,
    _vin_reg,
)
from tests.test_f050_m2_arreglos import _funcion, _node

ORIGEN = "parte PT26/00300 · 06/2026 · obra 0678"


def _rotulos(*llamadas: str) -> list:
    return _node("\n".join([
        _funcion("rotuloOrigen"),
        "process.stdout.write(JSON.stringify([" + ", ".join(llamadas)
        + "]));"]))


def test_f068_r20_rotulo_del_capitulo_ci4():
    assert _rotulos("rotuloOrigen('capitulo_ci4')",
                    "rotuloOrigen('capitulo_ci4', null)",
                    "rotuloOrigen('capitulo_ci4', 'x')") == [
        "capítulo CI.4 en empate", "capítulo CI.4 en empate",
        "capítulo CI.4 en empate: x"]


def test_f068_r20_los_demas_metodos_con_sus_rotulos_de_siempre():
    assert _rotulos(
        "rotuloOrigen('parte_anterior', " + repr(ORIGEN) + ")",
        "rotuloOrigen('ci_tipo')", "rotuloOrigen('auto_nombre')",
        "rotuloOrigen('auto_categoria')", "rotuloOrigen('titular')",
        "rotuloOrigen('otro')", "rotuloOrigen(null)") == [
        f"parte anterior: {ORIGEN}", "CI del tipo", "casada por nombre",
        "casada por categoría", "la del trabajador", "otro", ""]


@pytest.mark.parametrize("metodo, rotulo", [
    ("capitulo_ci4", "capítulo CI.4 en empate"),
    ("parte_anterior", "parte anterior"),
    ("auto_nombre", "casada por nombre")])
def test_f068_r20_la_subfila_rotula_su_propuesta(metodo, rotulo):
    v = {**TEL, "propuesta_cod": "CI.4.13", "propuesta_metodo": metodo}
    obs = _celdas(LINEA, v)
    assert f"CI.4.13 · TELEFONIA<span class=\"partida-metodo\"> · {rotulo}" \
        in obs["partida"]


@pytest.mark.parametrize("metodo, origen, rotulo", [
    ("capitulo_ci4", None, "capítulo CI.4 en empate"),
    ("parte_anterior", ORIGEN, f"parte anterior: {ORIGEN}")])
def test_f068_r20_el_modal_rotula_la_partida_del_vinculado(metodo, origen,
                                                          rotulo):
    obs = _modal_vin([_obra_reg([_accion_reg()], [_vin_reg(
        paride=82413, partida_cod="CI.4.13", partida_metodo=metodo,
        partida_origen=origen)])])
    _, tel = _filas_tabla(obs["html"])[:2]
    assert f'<div class="origen-partida">{rotulo}</div>' in tel
