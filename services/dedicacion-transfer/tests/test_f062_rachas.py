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


# ======================= T2: cadenas (D11, R11) ========================== #
from application.services.rachas import cadenas, propias  # noqa: E402
from domain.models.registro_models import IncidenciaEntrada  # noqa: E402


def _inc(id_=7, desde=5, hasta=9, codigo="CIV", *, recurso=200, mes=10,
         obra=40, **kw) -> IncidenciaEntrada:
    """Una incidencia del cuadrante de octubre de 2026 (el mes M)."""
    base = dict(id=id_, recurso_ide=recurso, empresa=1, codigo=codigo,
                ano=2026, mes=mes, desde=desde, hasta=hasta, paride=0,
                obra_ide=obra)
    base.update(kw)
    return IncidenciaEntrada(**base)


def _cad(c):
    return (c.recurso, c.codigo, c.duena.id, [m.id for m in c.miembros],
            c.desde, c.hasta)


def test_f062_d11_cadenas_pegadas_del_mismo_recurso_y_codigo():
    # C2: 5-9 y 12-16 (el 12 es lunes): una; 5-9 y 13-16: dos.
    assert [_cad(c) for c in cadenas([_inc(8, 12, 16), _inc(7, 5, 9)])] == [
        (200, "CIV", 7, [7, 8], 20261005, 20261016)]
    assert [_cad(c) for c in cadenas([_inc(7, 5, 9), _inc(8, 13, 16)])] == [
        (200, "CIV", 7, [7], 20261005, 20261009),
        (200, "CIV", 8, [8], 20261013, 20261016)]


def test_f062_d11_cadenas_entre_obras_y_tres_seguidas():
    incs = [_inc(9, 19, 23, obra=60), _inc(7, 5, 9, obra=40),
            _inc(8, 12, 16, obra=60)]
    [c] = cadenas(incs)
    assert _cad(c) == (200, "CIV", 7, [7, 8, 9], 20261005, 20261023)
    assert c.duena.obra_ide == 40


def test_f062_r8_cadenas_por_codigo_y_por_recurso():
    incs = [_inc(7, 5, 9), _inc(8, 12, 16, "CIB"), _inc(9, 12, 16, recurso=400)]
    assert [_cad(c) for c in cadenas(incs)] == [
        (200, "CIB", 8, [8], 20261012, 20261016),
        (200, "CIV", 7, [7], 20261005, 20261009),
        (400, "CIV", 9, [9], 20261012, 20261016)]


def test_f062_r11_cadenas_la_que_tiene_traza_no_se_une_a_la_anterior():
    for traza in ({"hmores_ide_ini": 51}, {"hmores_ide_fin": 52}):
        assert [_cad(c) for c in cadenas([_inc(7, 5, 9),
                                           _inc(8, 12, 16, **traza)])] == [
            (200, "CIV", 7, [7], 20261005, 20261009),
            (200, "CIV", 8, [8], 20261012, 20261016)]
    # La dueña sí puede tener traza: es la siguiente la que no se une.
    [c] = cadenas([_inc(7, 5, 9, hmores_ide_ini=51), _inc(8, 12, 16)])
    assert _cad(c)[3] == [7, 8]


def test_f062_r11_cadenas_sin_recurso_o_con_dias_imposibles_no_cuentan():
    incs = [_inc(7, 5, 9, recurso=None), _inc(8, 10, 9), _inc(9, 0, 3),
            _inc(10, 30, 32), _inc(11, None, 9), _inc(12, 5, 9)]
    assert [c.duena.id for c in cadenas(incs)] == [12]


def test_f062_d11_cadenas_un_solape_no_es_pegado():
    # La api no deja solapes (F-030 R18); si llegara uno, dos cadenas.
    assert len(cadenas([_inc(7, 5, 9), _inc(8, 9, 12)])) == 2


# ============================ T2: propias (R15) ========================== #
SK_INI, SK_FIN = "porcentajes:inc:7:ini", "porcentajes:inc:7:fin"


def test_f062_r15_propias_por_synckey_del_recurso():
    lineas = [_l(51, 20261005, sk=SK_INI), _l(52, 20261009, "CIZ", sk=SK_FIN),
              _l(53, 20261009, "CIZ", sk=SK_FIN, reside=400)]
    [c] = cadenas([_inc()])
    assert {r: ls.ide for r, ls in propias(c, lineas).items()} == {
        "ini": 51, "fin": 52}


def test_f062_r15_propias_por_ide_de_la_traza_con_nuestra_synckey():
    lineas = [_l(51, 20261006, sk=SK_INI), _l(60, 20261009, "CIZ", sk=SK_FIN)]
    [c] = cadenas([_inc(hmores_ide_ini=51, hmores_ide_fin=52)])
    # Sin la línea 52 en Sigrid, el `fin` se busca por su `synckey`.
    assert {r: ls.ide for r, ls in propias(c, lineas).items()} == {
        "ini": 51, "fin": 60}


def test_f062_r15_propias_por_ide_que_no_es_nuestra_no_vale():
    lineas = [_l(51, 20261005, sk=None), _l(52, 20261009, "CIZ", reside=400,
                                             sk=SK_FIN)]
    [c] = cadenas([_inc(hmores_ide_ini=51, hmores_ide_fin=52)])
    assert propias(c, lineas) == {}


def test_f062_r15_propias_el_ciz_ajeno_movido_por_su_ide():
    ajeno = _l(70, 20261009, "CIZ", sk="partes:9", parte="PT26/00040")
    [c] = cadenas([_inc(hmores_ide_fin=70, dia_fin_antes=7)])
    assert propias(c, [ajeno]) == {"fin": ajeno}
    # Sin `dia_fin_antes` un `CIZ` ajeno no es propio; y un inicio, nunca.
    [c] = cadenas([_inc(hmores_ide_fin=70)])
    assert propias(c, [ajeno]) == {}
    civ = _l(70, 20261009, "CIV", sk="partes:9")
    [c] = cadenas([_inc(hmores_ide_fin=70, dia_fin_antes=7)])
    assert propias(c, [civ]) == {}


def test_f062_r15_propias_solo_las_de_la_duena():
    lineas = [_l(51, 20261012, sk="porcentajes:inc:8:ini")]
    [c] = cadenas([_inc(7, 5, 9), _inc(8, 12, 16)])
    assert propias(c, lineas) == {}
