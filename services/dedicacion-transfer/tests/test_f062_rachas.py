# tests/test_f062_rachas.py
"""F-062 · El modelo puro de las rachas (`application/services/rachas.py`).

Sin red ni BBDD. Fechas de 2026: el 1 de octubre es jueves, el 12 lunes (el
festivo no cuenta, F-059), el 31 sábado y el 1 de noviembre domingo. Los
`ide` son inventados y no coinciden con ningún dato real.
"""
from __future__ import annotations

import pytest
from application.services.rachas import emparejar, llega_a_fin, pegado
from domain.models.registro_models import LineaIncidenciaSigrid


def _l(ide, fec, cod="CIV", *, reside=200, sk=None, parte="PT26/00100",
       hmoide=100, est=1, can=0.0, **kw) -> LineaIncidenciaSigrid:
    """Una línea `CI*`/`CIZ` leída de Sigrid."""
    return LineaIncidenciaSigrid(ide=ide, reside=reside, fecha_int=fec,
                                 hora_codigo=cod, synckey=sk, parte_cod=parte,
                                 can=can, hmoide=hmoide, parte_est=est, **kw)


# ============================ T1: pegado (D2) ============================ #
@pytest.mark.parametrize("c, d", [
    (20261009, 20261012),   # viernes 9 → lunes 12: sábado y domingo en medio
    (20261009, 20261010),   # al día siguiente: nada en medio
    (20261009, 20261011),   # viernes → domingo: solo el sábado en medio
    (20261030, 20261102),   # viernes 30-oct → lunes 2-nov: 31 sáb, 1 dom
    (20260930, 20261001),   # último día de septiembre → 1 de octubre
])
def test_f062_d2_pegado_solo_fines_de_semana_en_medio(c, d):
    assert pegado(c, d) is True


@pytest.mark.parametrize("c, d", [
    (20261009, 20261013),   # el lunes 12 (festivo, pero laborable aquí)
    (20261009, 20261009),   # el mismo día no está pegado
    (20261012, 20261009),   # al revés
    (20261008, 20261012),   # el viernes 9 en medio
    (20261029, 20261102),   # el viernes 30 en medio
])
def test_f062_d2_no_pegado_con_un_laborable_en_medio_o_al_reves(c, d):
    assert pegado(c, d) is False


# ========================== T1: llega_a_fin (D7) ========================= #
@pytest.mark.parametrize("h, sale", [
    (20261031, True),       # el último día
    (20261030, True),       # viernes 30: solo queda el sábado 31
    (20261029, False),      # jueves 29: queda el viernes 30
    (20260930, True),       # septiembre acaba en miércoles 30
    (20260929, False),
    (20261127, False),      # viernes 27-nov: el lunes 30 aún es del mes
])
def test_f062_d7_llega_a_fin_de_mes(h, sale):
    assert llega_a_fin(h) is sale


def test_f062_d7_llega_a_fin_un_mes_que_acaba_en_domingo():
    # Mayo de 2026 acaba en domingo 31: el viernes 29 ya llega.
    assert llega_a_fin(20260529) is True
    assert llega_a_fin(20260528) is False


# ========================== T1: emparejar (D5) =========================== #
def test_f062_d5_emparejar_inicio_y_su_ciz():
    [r] = emparejar([_l(2, 20261009, "CIZ"), _l(1, 20261005)])
    assert (r.codigo, r.inicio.ide, r.cierre.ide) == ("CIV", 1, 2)


def test_f062_d5_emparejar_el_ciz_cierra_el_abierto_mas_reciente():
    lineas = [_l(1, 20261001, "CIE"), _l(2, 20261005, "CIV"),
              _l(3, 20261007, "CIZ"), _l(4, 20261009, "CIZ")]
    assert [(r.codigo, r.inicio.ide, r.cierre.ide) for r in emparejar(lineas)] \
        == [("CIE", 1, 4), ("CIV", 2, 3)]


def test_f062_d5_emparejar_el_mismo_dia_el_inicio_antes_que_el_ciz():
    # Racha de un día (E-7): inicio y CIZ el mismo día, sea cual sea su `ide`.
    [r] = emparejar([_l(9, 20261005, "CIZ"), _l(10, 20261005)])
    assert (r.inicio.ide, r.cierre.ide) == (10, 9)


def test_f062_d5_emparejar_por_ide_a_igual_fec_y_papel():
    lineas = [_l(5, 20261005, "CIV"), _l(4, 20261005, "CIE"),
              _l(6, 20261006, "CIZ")]
    # Orden (fec, inicio antes que CIZ, ide): CIE 4, CIV 5, CIZ 6 cierra el 5.
    assert [(r.inicio.ide, r.cierre.ide if r.cierre else None)
            for r in emparejar(lineas)] == [(4, None), (5, 6)]


def test_f062_d5_emparejar_ciz_huerfano_no_forma_racha_y_abierta_sin_ciz():
    lineas = [_l(1, 20261002, "CIZ"), _l(2, 20261005, "CIB")]
    [r] = emparejar(lineas)
    assert (r.codigo, r.inicio.ide, r.cierre) == ("CIB", 2, None)


def test_f062_d5_emparejar_por_recurso_y_sin_lineas_que_no_son_ci():
    lineas = [_l(1, 20261005, reside=200), _l(2, 20261007, "CIZ", reside=400),
              _l(3, 20261008, "CIZ", reside=200), _l(4, 20261006, "MENC"),
              _l(5, 20261006, None), _l(6, 20261006, " CIZ ", reside=400)]
    assert [(r.inicio.ide, r.cierre.ide) for r in emparejar(lineas)] == [(1, 3)]


def test_f062_d5_emparejar_cruza_meses_y_ordena_por_inicio():
    lineas = [_l(3, 20261106, "CIZ"), _l(1, 20261027), _l(7, 20260915, "CIE"),
              _l(8, 20261002, "CIZ")]
    assert [(r.inicio.ide, r.cierre.ide) for r in emparejar(lineas)] == [
        (7, 8), (1, 3)]
