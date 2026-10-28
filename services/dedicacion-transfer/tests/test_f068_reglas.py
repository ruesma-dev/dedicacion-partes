# tests/test_f068_reglas.py
"""F-068 · la partida del vinculado como la del trabajador, reglas puras
(`application/services/reglas_vinculados.py`; design §6.1).

- R5-R8 (T2): las piezas: las hojas activas con su cuenta
  (`hojas_con_subcuenta`), el capítulo CI.4 por número (`es_capitulo_ci4`),
  la puntuación del casador una a una (`puntuar`) y el desempate por el
  capítulo CI.4 (`desempate_ci4`).

Fixture «de la 0678» con `ide` inventados: cada cuenta de los vinculados
(`CICO13`, `CICO01`, `CICO15`, `CIMP09`) en dos hojas, una del capítulo
`CI.0` (o `CI.03P`) y otra del `CI.4`, con la misma descripción. Sin red ni
BBDD.
"""
from __future__ import annotations

import pytest
from application.services.partida_resolver import construir_catalogo
from application.services.reglas_vinculados import (
    desempate_ci4,
    es_capitulo_ci4,
    hojas_con_subcuenta,
    puntuar,
)

from tests.conftest import _fila

PRESUPUESTO = [
    _fila(60000, 0, 0, "CI", "COSTES INDIRECTOS"),
    _fila(60100, 60000, 1, "CI.0", "CAPITULO 0"),
    _fila(60101, 60100, 1, "CI.0.13", "TELEFONIA"),
    _fila(60102, 60100, 2, "CI.0.01", "COMBUSTIBLE"),
    _fila(60103, 60100, 3, "CI.0.06", "VEHICULOS"),
    _fila(60104, 60100, 4, "CI.0.15", "VARIOS"),
    _fila(60105, 60100, 5, "CI.0.20", "LIMPIEZA"),
    _fila(60400, 60000, 2, "CI.4", "CAPITULO 4"),
    _fila(60401, 60400, 1, "CI.4.13", "TELEFONIA"),
    _fila(60402, 60400, 2, "CI.4.1", "COMBUSTIBLE"),
    _fila(60403, 60400, 3, "CI.4.15", "VARIOS"),
    _fila(60404, 60400, 4, "CI.4.99", "TELEFONIA", tipdes=1),
    _fila(60405, 60400, 5, "CI.4.20", "MENSAJERIA"),
    _fila(60406, 60400, 6, "CI.04.21", "MENSAJERIA"),
    _fila(60300, 60000, 3, "CI.03P", "CAPITULO 3P"),
    _fila(60301, 60300, 1, "CI.03P.9", "VEHICULOS"),
    _fila(60302, 60300, 2, "CI.03P.20", "LIMPIEZA"),
    _fila(60500, 60000, 4, "CI.5", "PERSONAL"),
    _fila(60501, 60500, 1, "CI.5.1", "JEFE DE OBRA"),
    _fila(60502, 60500, 2, "CI.5.2", "TELEFONO MOVIL ENCARGADO"),
    _fila(60503, 60500, 3, "CI.5.3", "VEHICULO FURGONETA"),
    _fila(60504, 60500, 4, "CI.5.4", "GASOIL VEHICULOS"),
    _fila(60800, 0, 5, "CP", "COSTES PROPORCIONALES"),
    _fila(60801, 60800, 1, "CP.1", "VARIOS CP"),
    _fila(60900, 0, 6, "CD", "COSTES DIRECTOS"),
    _fila(60901, 60900, 1, "CD.1", "HORMIGON"),
]
#: Cuenta de cada partida que la tiene (la de baja 60404 y el capítulo
#: 60400 con `CICO13`: no cuentan).
CUENTAS = {
    60101: "0678.CICO13", 60401: "0678.CICO13", 60404: "0678.CICO13",
    60400: "0678.CICO13",
    60102: "0678.CICO01", 60402: "0678.CICO01",
    60104: "0678.CICO15", 60403: "0678.CICO15",
    60103: "0678.CIMP09", 60301: "0678.CIMP09",
    60405: "0678.CIME20", 60406: "0678.CIME20",
    60503: "0678.CIVE20", 60504: "0678.CIVE20",
    60501: "0678.CIMO01",
    60901: "0678.CD.1",
}


def _hojas():
    return construir_catalogo(PRESUPUESTO)


def _n(*ides: int):
    h = _hojas()
    return [h[i] for i in ides]


# ================================ R8 ===================================== #
@pytest.mark.parametrize("cod", [
    "CI.4.13", "CI.04.13", "CI.4.19_1", "CI.4", "ci.4.1", " CI.4.1 ",
    "CI-.4.1", "CI.004.2"])
def test_f068_r8_es_del_capitulo_ci4(cod):
    assert es_capitulo_ci4(cod) is True


@pytest.mark.parametrize("cod", [
    "CI0.04.05", "CI_F1.04.10", "CI.0.17", "CI.03P.9", "CI.40.1", "CI.14.1",
    "CI..4", "CI", "CI4.1", "CD.4.1", "XCI.4.1", "CI.4A.1", "CI.²", None,
    ""])
def test_f068_r8_no_es_del_capitulo_ci4(cod):
    assert es_capitulo_ci4(cod) is False


# ================================ R5 ===================================== #
def test_f068_r5_hojas_activas_con_su_cuenta_en_orden():
    """Las dos hojas activas con `CICO13`; ni la de baja ni el capítulo."""
    assert [n.ide for n in hojas_con_subcuenta(
        _hojas(), CUENTAS, "CICO13")] == [60101, 60401]
    assert [n.ide for n in hojas_con_subcuenta(
        _hojas(), CUENTAS, " cimo01 ")] == [60501]


@pytest.mark.parametrize("sub", [None, "", "  ", "CIZZ99", "CICO1"])
def test_f068_r5_sin_su_cuenta_ninguna(sub):
    assert hojas_con_subcuenta(_hojas(), CUENTAS, sub) == []


def test_f068_r5_cuenta_de_una_partida_fuera_del_presupuesto():
    assert hojas_con_subcuenta(_hojas(), {99999: "X.CICO13"}, "CICO13") == []


def test_f068_r5_puntua_una_a_una_y_el_empate_se_ve():
    """Pasadas juntas, el casador se quedaría con la primera; una a una,
    las dos puntúan lo mismo."""
    assert puntuar(_n(60101, 60401), "TELEFONIA", "MOVIL 600",
                   solo_casadas=False) == {
        60101: (0.9, "auto_categoria"), 60401: (0.9, "auto_categoria")}


def test_f068_r5_categoria_es_tipo_res_y_nombre_la_descripcion():
    p = puntuar(_n(60503, 60504), "VEHICULO", "FURGONETA 1234ABC",
                solo_casadas=False)
    assert p == {60503: (1.0, "auto_nombre"), 60504: (0.9, "auto_categoria")}
    # Al revés no casa igual: la categoría es el tipo y el nombre, la
    # descripción.
    assert puntuar(_n(60502), None, "TELEFONO MOVIL ENCARGADO",
                   solo_casadas=True) == {60502: (0.92, "auto_nombre")}


def test_f068_r5_la_que_no_casa_puntua_cero():
    assert puntuar(_n(60101, 60401), None, None, solo_casadas=False) == {
        60101: (0.0, None), 60401: (0.0, None)}
    assert puntuar(_n(60101, 60502), "TELEFONO", "TELEFONO MOVIL 600",
                   solo_casadas=False) == {
        60101: (0.0, None), 60502: (1.0, "auto_nombre")}


def test_f068_r6_solo_casadas_deja_fuera_las_que_no_casan():
    assert puntuar(_n(60101, 60502), "TELEFONO", "TELEFONO MOVIL 600",
                   solo_casadas=True) == {60502: (1.0, "auto_nombre")}
    assert puntuar(_n(60101, 60401), None, None, solo_casadas=True) == {}


# ================================ R7 ===================================== #
def test_f068_r7_desempate_la_unica_del_ci4():
    assert desempate_ci4(_n(60101, 60401)).ide == 60401
    assert desempate_ci4(_n(60401, 60101)).ide == 60401
    assert desempate_ci4(_n(60406, 60103)).ide == 60406


@pytest.mark.parametrize("ides", [
    (60103, 60301), (60405, 60406), (60401, 60402, 60101), (60101,), ()])
def test_f068_r7_ninguna_o_varias_del_ci4_no_desempata(ides):
    assert desempate_ci4(_n(*ides)) is None
