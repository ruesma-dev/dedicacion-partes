# tests/test_f051_reglas_cero.py
"""F-051 · Funciones puras de las líneas al 0 % (R1, R2, R7, R9; design §5).

Una línea es **pisable** para una acción `escribir` si es del mismo recurso,
`M*` y con `can` 0 o nulo, no vive en un parte cerrado, no es de esta
ejecución y, en postventa, tiene la partida de la acción (R1). Cada acción
edita como mucho una (R2). La `synckey` de otro sistema no se cambia (R9).
Sin I/O: ni cliente, ni ajustes, ni red.
"""
from __future__ import annotations

import random

import pytest
from application.services.reglas_porcentajes import (
    emparejar_ceros,
    es_linea_al_cero,
    es_nuestra_de_otra,
    pisables_al_cero,
    repartir_choques,
    synckey_tras_editar,
)
from domain.models.registro_models import AccionLinea

from tests.conftest import linea_previa

SK_MIA = "porcentajes:1"


def _cero(ide: int, **kw):
    """Línea `M*` al 0 % de Administración (copia del mes anterior)."""
    datos = dict(ide=ide, reside=200, fecha_int=20261031, horide=5,
                 hora_codigo="MENC", can=0.0, tot=0.0, synckey=None,
                 paride=80001)
    datos.update(kw)
    return linea_previa(**datos)


def _accion(registro_id: int = 1, **kw) -> AccionLinea:
    datos = dict(registro_id=registro_id, accion="escribir", ano=2026,
                 mes=10, fecha_int=20261031, recurso_ide=200, hora_ide=5,
                 hora_codigo="MENC", can=0.4, pre=9000.0, tot=3600.0,
                 paride=80001, partida_cod="CI.1.10")
    datos.update(kw)
    return AccionLinea(**datos)


def _pisables(existentes, accion, *, en_cerrado=frozenset(), mias=None):
    return [ls.ide for ls in pisables_al_cero(
        existentes, accion, en_cerrado=set(en_cerrado),
        mias=set(mias or ()))]


# ================================ R1 =================================== #
@pytest.mark.parametrize("can", [0, 0.0, None])
def test_f051_r1_can_cero_o_nulo_es_al_cero(can):
    assert es_linea_al_cero(_cero(1, can=can)) is True


@pytest.mark.parametrize("can", [0.0001, 1.0, -0.5])
def test_f051_r1_can_distinto_de_cero_no(can):
    """D4: `can` exacto 0 o nulo, sin tolerancia."""
    assert es_linea_al_cero(_cero(1, can=can)) is False


@pytest.mark.parametrize("hora", ["HLPE", "CTRA", "OTEL", "KM", None, ""])
def test_f051_r1_r7_hora_no_mensual_no_es_al_cero(hora):
    assert es_linea_al_cero(_cero(1, hora_codigo=hora)) is False


@pytest.mark.parametrize("hora", ["MENC", "MADM", "mcap", "M"])
def test_f051_r1_cualquier_m_es_al_cero(hora):
    assert es_linea_al_cero(_cero(1, hora_codigo=hora)) is True


@pytest.mark.parametrize("reside", [0, None])
def test_f051_r1_sin_recurso_no_es_al_cero(reside):
    assert es_linea_al_cero(_cero(1, reside=reside)) is False


def test_f051_r1_cualquier_m_y_partida_en_obra_normal():
    """D3 = A: cualquier `M*` al 0 % del recurso, de cualquier partida, en
    la obra normal; por `ide`."""
    existentes = [_cero(30, paride=99999, horide=8, hora_codigo="MADM"),
                  _cero(10), _cero(20, paride=0)]
    assert _pisables(existentes, _accion()) == [10, 20, 30]


def test_f051_r1_postventa_solo_misma_partida():
    """D7 = B: en postventa, solo la de la partida de la acción."""
    existentes = [_cero(10, paride=70001), _cero(20, paride=80001),
                  _cero(30, paride=0)]
    a = _accion(destino="postventa", es_postventa=True, paride=70001)
    assert _pisables(existentes, a) == [10]


def test_f051_r1_r7_otro_recurso_no():
    assert _pisables([_cero(10, reside=400)], _accion()) == []


@pytest.mark.parametrize("hora", ["HLPE", "CTRA", "OTEL", "KM"])
def test_f051_r1_r7_horas_no_m_no(hora):
    assert _pisables([_cero(10, hora_codigo=hora)], _accion()) == []


def test_f051_r1_r7_en_parte_cerrado_no():
    existentes = [_cero(10), _cero(20)]
    assert _pisables(existentes, _accion(), en_cerrado={10}) == [20]


def test_f051_r1_de_esta_ejecucion_no():
    """D5: las de esta ejecución (`mias`) no; las nuestras de otra
    asignación y las de otro sistema, sí."""
    existentes = [_cero(10, synckey=SK_MIA),
                  _cero(20, synckey="porcentajes:77"),
                  _cero(30, synckey="partes:abc")]
    assert _pisables(existentes, _accion(), mias={SK_MIA}) == [20, 30]


def test_f051_r1_no_al_cero_no():
    assert _pisables([_cero(10, can=0.5)], _accion()) == []


# ================================ R2 =================================== #
def test_f051_r2_una_por_accion_misma_partida_primero():
    existentes = [_cero(10, paride=99999), _cero(20), _cero(30, paride=99999)]
    pares, sobran = emparejar_ceros([_accion()], existentes,
                                    en_cerrado=set(), mias=set())
    assert {r: ls.ide for r, ls in pares.items()} == {1: 20}
    assert sobran == {200: 2}


def test_f051_r2_sin_misma_partida_misma_hora():
    existentes = [_cero(10, paride=99999, horide=8, hora_codigo="MADM"),
                  _cero(20, paride=99998)]
    pares, _ = emparejar_ceros([_accion()], existentes, en_cerrado=set(),
                               mias=set())
    assert pares[1].ide == 20


def test_f051_r2_empate_menor_ide():
    existentes = [_cero(30, paride=99999), _cero(20, paride=99998)]
    pares, sobran = emparejar_ceros([_accion()], existentes,
                                    en_cerrado=set(), mias=set())
    assert pares[1].ide == 20 and sobran == {200: 1}


def test_f051_r2_dos_acciones_una_pisable_una_edita_otra_inserta():
    """Acciones por `registro_id`: la menor se lleva la pisable."""
    acciones = [_accion(7, paride=99999), _accion(3, paride=99999)]
    pares, sobran = emparejar_ceros(acciones, [_cero(10)], en_cerrado=set(),
                                    mias=set())
    assert {r: ls.ide for r, ls in pares.items()} == {3: 10}
    assert sobran == {200: 0}


def test_f051_r2_dos_acciones_dos_pisables_cada_una_la_suya():
    acciones = [_accion(1, paride=80002), _accion(2)]
    existentes = [_cero(10), _cero(20, paride=80002)]
    pares, sobran = emparejar_ceros(acciones, existentes, en_cerrado=set(),
                                    mias=set())
    assert {r: ls.ide for r, ls in pares.items()} == {1: 20, 2: 10}
    assert sobran == {200: 0}


def test_f051_r2_dos_pisables_una_accion_una_queda_a_cero_por_recurso():
    acciones = [_accion(1), _accion(2, recurso_ide=400, hora_ide=6)]
    existentes = [_cero(10), _cero(11), _cero(20, reside=400, horide=6),
                  _cero(21, reside=400, horide=6),
                  _cero(22, reside=400, horide=6)]
    pares, sobran = emparejar_ceros(acciones, existentes, en_cerrado=set(),
                                    mias=set())
    assert {r: ls.ide for r, ls in pares.items()} == {1: 10, 2: 20}
    assert sobran == {200: 1, 400: 2}


def test_f051_r2_respeta_cerrados_y_mias():
    existentes = [_cero(10), _cero(20, synckey=SK_MIA), _cero(30)]
    pares, sobran = emparejar_ceros([_accion()], existentes, en_cerrado={10},
                                    mias={SK_MIA})
    assert pares[1].ide == 30 and sobran == {200: 0}


def test_f051_r2_sin_pisables_no_empareja():
    pares, sobran = emparejar_ceros([_accion()], [_cero(10, can=1.0)],
                                    en_cerrado=set(), mias=set())
    assert pares == {} and sobran == {200: 0}


def test_f051_r2_filas_barajadas_mismo_emparejado():
    acciones = [_accion(i, paride=80001 + (i % 3)) for i in range(1, 6)]
    existentes = [_cero(100 + i, paride=80001 + (i % 4),
                        horide=5 if i % 2 else 8) for i in range(9)]
    base = emparejar_ceros(acciones, existentes, en_cerrado=set(), mias=set())
    azar = random.Random(20261020)
    for _ in range(20):
        a, e = list(acciones), list(existentes)
        azar.shuffle(a)
        azar.shuffle(e)
        assert emparejar_ceros(a, e, en_cerrado=set(), mias=set()) == base


# ============================ R4 · R5 ================================== #
def test_f051_r4_r5_un_registro_edita_el_menor_y_los_demas_a_cero():
    choques = [_cero(30, can=1), _cero(10, can=1), _cero(20, can=1)]
    assert repartir_choques([9], choques) == ({9: 10}, [20, 30])


def test_f051_r4_dos_registros_cada_uno_un_choque_por_registro_id():
    choques = [_cero(30, can=1), _cero(10, can=1), _cero(20, can=1)]
    assert repartir_choques([9, 4], choques) == ({4: 10, 9: 20}, [30])


def test_f051_r4_mas_registros_que_choques():
    assert repartir_choques([2, 1], [_cero(10, can=1)]) == ({1: 10}, [])


# ================================ R9 =================================== #
@pytest.mark.parametrize("actual", [None, "", "   ", "porcentajes:77",
                                    " porcentajes:1 "])
def test_f051_r9_vacia_o_nuestra_pasa_a_la_nueva(actual):
    assert synckey_tras_editar(actual, "porcentajes:5") == "porcentajes:5"


@pytest.mark.parametrize("actual", ["partes:2026-10-03:410600", "otro",
                                    "PORCENTAJES:1", "x porcentajes:1"])
def test_f051_r9_la_de_otro_sistema_se_conserva(actual):
    assert synckey_tras_editar(actual, "porcentajes:5") == actual.strip()


# ============================ R15 (pura) =============================== #
@pytest.mark.parametrize("sk, esperado", [
    ("porcentajes:2", True), (" porcentajes:2 ", True),
    ("porcentajes:1", False), (None, False), ("", False),
    ("partes:abc", False),
])
def test_f051_r15_nuestra_de_otra_asignacion(sk, esperado):
    assert es_nuestra_de_otra(sk, "porcentajes:1") is esperado
