# tests/test_f055_orden_propuesta.py
"""F-055 · R38 (D10): el orden de la propuesta es a → c → b.

(a) parte anterior del recurso en esa obra; (c) casamiento por nombre y
categoría (`resolver_normal`, `auto_*`); (b) último parte en otra obra,
trasladado por código y descripción. Pasos, reglas y métodos de F-050 no
cambian; solo el orden. Vale en `proponer_partida`, en el selector
(`POST /api/partidas/propuesta`) y en el preflight.

Sin red ni BBDD; los `ide` son inventados.
"""
from __future__ import annotations

import pytest
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.propuesta_partida import (
    Propuesta,
    proponer_partida,
)
from domain.models.registro_models import ObraEntrada

from tests.conftest import OBRA_ORIGEN, SettingsFalso, linea
from tests.test_f050_endpoint_propuesta import (  # noqa: F401 (fixture)
    RUTA,
    ClienteSoloLectura,
    _l,
    _peticion,
    api,
)
from tests.test_f050_pipeline import ClienteHistorial
from tests.test_f050_pipeline import _h as _h_pipeline
from tests.test_f050_propuesta import OBRA, OTRA, RECURSO, _h, _nodos

#: Categoría y nombre que casan (`auto_nombre`, 2108 «ENCARGADO (ACUNA)»).
CASA = ("Encargado", "Acuna Mera, Antonio")
#: Categoría y nombre que no casan con ninguna hoja.
NO_CASA = ("Astronauta", "Nadie Nunca")


# ================== R38 · proponer_partida, paso a paso ================== #
def test_f055_r38_a_gana_a_c():
    hist = [_h(mes=5)]                                  # parte anterior
    p = proponer_partida(_nodos(), hist, RECURSO, OBRA, *CASA)
    assert (p.paride, p.metodo) == (2105, "parte_anterior")


def test_f055_r38_c_gana_a_b():
    hist = [_h(obra=OTRA, paride=88001, cod="CI.1.9",
               res="ADMINISTRATIVO")]                   # último parte
    p = proponer_partida(_nodos(), hist, RECURSO, OBRA, *CASA)
    assert p == Propuesta(paride=2108, cod="CI.1.8",
                          res="ENCARGADO (ACUNA)", metodo="auto_nombre",
                          origen=None)


def test_f055_r38_sin_c_sale_b_con_su_origen():
    hist = [_h(obra=OTRA, paride=88001, cod="CI.1.9", res="ADMINISTRATIVO",
               parte="PT26/00777", obra_cod="0696")]
    p = proponer_partida(_nodos(), hist, RECURSO, OBRA, *NO_CASA)
    assert p == Propuesta(paride=2109, cod="CI.1.9", res="ADMINISTRATIVO",
                          metodo="ultimo_parte",
                          origen="parte PT26/00777 · 09/2026 · obra 0696")


def test_f055_r38_sin_nada_none():
    hist = [_h(obra=OTRA, paride=88001, cod="ZZ.9", res="NADA")]
    assert proponer_partida(_nodos(), hist, RECURSO, OBRA, *NO_CASA) is None
    assert proponer_partida(_nodos(), [], RECURSO, OBRA, *NO_CASA) is None


def test_f055_r38_a_gana_aunque_no_case():
    """(a) va primero también cuando el casamiento no daría nada."""
    p = proponer_partida(_nodos(), [_h(mes=5)], RECURSO, OBRA, *NO_CASA)
    assert (p.paride, p.metodo) == (2105, "parte_anterior")


def test_f055_r38_a_que_no_propone_pasa_a_c_no_a_b():
    """Un empate en (a) no propone: decide (c), aunque (b) daría algo."""
    hist = [_h(mes=9, can=0.5), _h(mes=9, can=0.5, paride=2109,
                                   cod="CI.1.9"),
            _h(obra=OTRA, paride=88001, cod="CI.1.10", res="TOPOGRAFO")]
    p = proponer_partida(_nodos(), hist, RECURSO, OBRA, *CASA)
    assert (p.paride, p.metodo) == (2108, "auto_nombre")


# ========== R38 · selector y preflight dan lo mismo con el orden ========= #
#: Historial solo en otra obra: (b) daría 80003 (CI.1.9) trasladada.
HIST_OTRA = [_h_pipeline(obra=696, paride=88003)]


@pytest.mark.parametrize("categoria, nombre, esperado", [
    (*CASA, (80001, "auto_nombre", None)),
    (*NO_CASA, (80003, "ultimo_parte",
                "parte PT26/00100 · 07/2026 · obra 0678")),
], ids=["c_gana_a_b", "sin_c_sale_b"])
def test_f055_r38_selector_y_preflight_dan_lo_mismo(
        api, categoria, nombre, esperado):  # noqa: F811
    cuerpo = api(ClienteSoloLectura(HIST_OTRA)).post(RUTA, json=_peticion(
        _l("1", categoria=categoria, nombre=nombre))).json()
    pf = RegistroPipeline(cliente=ClienteHistorial(HIST_OTRA),
                          settings=SettingsFalso()).preflight(
        obra=ObraEntrada(codigo=OBRA_ORIGEN),
        lineas=[linea(categoria=categoria, nombre=nombre)])
    a = pf.acciones[0]
    propuesta = cuerpo["propuestas"]["1"]
    assert (propuesta["paride"], propuesta["metodo"],
            propuesta["origen"]) == esperado
    assert (a.paride, a.partida_metodo, a.partida_origen) == esperado
