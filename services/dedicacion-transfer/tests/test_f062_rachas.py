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
       hmoide=100, est=1, can=0.0, parte_emp=1, **kw
       ) -> LineaIncidenciaSigrid:
    """Una línea `CI*`/`CIZ` leída de Sigrid."""
    return LineaIncidenciaSigrid(ide=ide, reside=reside, fecha_int=fec,
                                 hora_codigo=cod, synckey=sk, parte_cod=parte,
                                 can=can, hmoide=hmoide, parte_est=est,
                                 parte_emp=parte_emp, **kw)


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
from application.services.rachas import cadenas, propias
from domain.models.registro_models import IncidenciaEntrada


def _inc(id_=7, desde=5, hasta=9, codigo="CIV", *, recurso=200, mes=10,
         obra=40, **kw) -> IncidenciaEntrada:
    """Una incidencia del cuadrante de octubre de 2026 (el mes M)."""
    base = {"id": id_, "recurso_ide": recurso, "empresa": 1,
            "codigo": codigo, "ano": 2026, "mes": mes, "desde": desde,
            "hasta": hasta, "paride": 0, "obra_ide": obra}
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


# ========================= T3: previa (R1, R10) ========================== #
from application.services.rachas import previa

EST = 1


def _previa(lineas, *incs, pruebas=None):
    [c] = cadenas(list(incs))
    r, avisos = previa(emparejar(lineas), c, est=EST, obride_pruebas=pruebas)
    return (r.inicio.ide if r else None), avisos


def test_f062_r1c_c2_previa_con_su_ciz_pegado_a_d():
    lineas = [_l(1, 20261005), _l(2, 20261009, "CIZ")]
    assert _previa(lineas, _inc(8, 12, 16)) == (1, [])     # 10-11, fin de semana
    assert _previa(lineas, _inc(8, 13, 16)) == (None, [])  # el lunes 12 corta


def test_f062_r1c_c6_previa_con_su_ciz_en_d_o_despues():
    lineas = [_l(1, 20261005, obride=40), _l(2, 20261007, "CIZ", obride=40)]
    assert _previa(lineas, _inc(7, 5, 9, obra=60)) == (1, [])
    lineas = [_l(1, 20261005), _l(2, 20261005, "CIZ")]
    assert _previa(lineas, _inc(7, 5, 9)) == (1, [])


def test_f062_r1a_previa_abierta_con_inicio_en_m():
    assert _previa([_l(1, 20261001)], _inc(7, 20, 23)) == (1, [])
    # Su CIZ en M+1 no la cierra en M (R21 avisará).
    lineas = [_l(1, 20261027), _l(2, 20261106, "CIZ")]
    assert _previa(lineas, _inc(7, 27, 30)) == (1, [])


def test_f062_r1b_c3_c5_previa_abierta_de_antes_pegada_al_fin_de_m1():
    # C3: CIV el 27-oct abierta; noviembre del 2 (el 1 es domingo).
    assert _previa([_l(1, 20261027)], _inc(8, 2, 6, mes=11)) == (1, [])
    # C5: CIE el 15-sep; octubre del 1 y noviembre del 1.
    cie = [_l(1, 20260915, "CIE")]
    assert _previa(cie, _inc(8, 1, 31, "CIE")) == (1, [])
    assert _previa(cie, _inc(9, 1, 10, "CIE", mes=11)) == (1, [])
    # Abierta de antes pero el tramo empieza a mitad de mes: no.
    assert _previa(cie, _inc(8, 5, 9, "CIE")) == (None, [])


def test_f062_r1_previa_del_mismo_codigo_e_inicio_no_posterior():
    lineas = [_l(1, 20261005, "CIB"), _l(2, 20261007, "CIZ")]
    assert _previa(lineas, _inc(7, 5, 9)) == (None, [])
    lineas = [_l(1, 20261007), _l(2, 20261009, "CIZ")]
    assert _previa(lineas, _inc(7, 5, 9)) == (None, [])
    # Un CIZ de M anterior a `d` y no pegado no la hace previa.
    lineas = [_l(1, 20261001), _l(2, 20261002, "CIZ")]
    assert _previa(lineas, _inc(7, 6, 9)) == (None, [])


def test_f062_r1_previa_de_varias_la_de_inicio_mas_reciente():
    lineas = [_l(1, 20261001), _l(3, 20261005), _l(4, 20261007, "CIZ")]
    assert _previa(lineas, _inc(7, 5, 9)) == (3, [])
    lineas = [_l(3, 20261002), _l(4, 20261006, "CIZ"), _l(1, 20261003)]
    # Pila: el CIZ del 6 cierra el del 3; el del 2 sigue abierto.
    assert _previa(lineas, _inc(7, 7, 9)) == (1, [])


def test_f062_r10_c8_previa_no_con_ciz_del_mes_anterior_y_avisa():
    lineas = [_l(1, 20260920), _l(2, 20260930, "CIZ", parte="PT26/00090")]
    ide, avisos = _previa(lineas, _inc(7, 1, 9))
    assert ide is None
    assert avisos == [("la racha CIV del 20/09 se cerró el 30/09 en el parte "
                      "PT26/00090 (línea 2), del mes anterior: se abre otra")]
    # Sin pegar (el 1 de octubre es jueves; del 2 ya no): sin aviso.
    assert _previa(lineas, _inc(7, 2, 9)) == (None, [])


def test_f062_r10_previa_no_si_su_ciz_no_se_puede_mover():
    cerrado = [_l(1, 20261005), _l(2, 20261007, "CIZ", est=3,
                                     parte="PT26/00041")]
    ide, avisos = _previa(cerrado, _inc(7, 5, 9))
    assert ide is None
    assert avisos == [("la racha CIV del 05/10 se cierra el 07/10 en el parte "
                      "PT26/00041 (línea 2), que no se puede mover: se abre "
                      "otra")]
    # Si no hay que moverlo (ya está en `h` o después), vale aunque esté
    # cerrado: la cubre.
    cubre = [_l(1, 20261005), _l(2, 20261009, "CIZ", est=3)]
    assert _previa(cubre, _inc(7, 5, 9)) == (1, [])
    # Llega a fin de mes: su CIZ iría al último día (R11), así que se mueve.
    lineas = [_l(1, 20261026), _l(2, 20261028, "CIZ", est=3)]
    assert _previa(lineas, _inc(7, 26, 30))[0] is None


def test_f062_r10_previa_no_en_pruebas_fuera_de_la_obra_de_pruebas():
    lineas = [_l(1, 20261005, obride=828942),
              _l(2, 20261007, "CIZ", obride=555001)]
    assert _previa(lineas, _inc(7, 5, 9), pruebas=828942)[0] is None
    lineas[1] = _l(2, 20261007, "CIZ", obride=828942)
    assert _previa(lineas, _inc(7, 5, 9), pruebas=828942) == (1, [])


# ===================== T4: decidir_cadena (R1-R11, …) ==================== #
from application.services.rachas import decidir_cadena
from application.services.reglas_incidencias import (
    MOTIVO_INC_CAMBIADA,
    decidir_incidencia,
)
from domain.models.registro_models import HoraRecurso

HORAS = {200: [HoraRecurso(71, "CIV", "Vacaciones(V)", 12.5),
               HoraRecurso(72, "CIE", "Baja(B)", 0.0),
               HoraRecurso(73, "CIB", "Permiso", 0.0),
               HoraRecurso(79, "CIZ", "Fin de Incidencia", 0.0)]}


def _decidir(lineas, *incs, est=EST, empresa=1, pruebas=None):
    """El plan de la (única) cadena de `incs`, con la base de su dueña."""
    [c] = cadenas(list(incs))
    base = decidir_incidencia(c.duena, HORAS)
    return decidir_cadena(c, lineas, base, est=est, empresa=empresa,
                          obride_pruebas=pruebas)


def _v(plan):
    """(id, rol, acción, fec, hmores_ide) de cada acción."""
    return [(a.id, a.rol, a.accion, a.fecha_int, a.hmores_ide)
            for a in plan.acciones]


def _r(plan):
    return [(r.id, r.papel, r.inicio_fec, r.cierre, r.cierre_fec, r.duena_id)
            for r in plan.resumenes]


def test_f062_c1_decidir_abre_y_cierra_en_el_mismo_parte():
    plan = _decidir([], _inc(7, 5, 9))
    assert _v(plan) == [(7, "ini", "escribir", 20261005, None),
                        (7, "fin", "escribir", 20261009, None)]
    ini, fin = plan.acciones
    assert (ini.hora_codigo, fin.hora_codigo, fin.hmoide_destino) == (
        "CIV", "CIZ", None)          # los dos, al parte del paso 5 (R2)
    assert _r(plan) == [(7, "abre", 20261005, "cierra", 20261009, 7)]
    assert plan.resumenes[0].avisos == []


def test_f062_r8_decidir_la_no_duena_continua_en_la_cadena():
    plan = _decidir([], _inc(7, 5, 9), _inc(8, 12, 16, obra=60))
    assert _v(plan) == [(7, "ini", "escribir", 20261005, None),
                        (7, "fin", "escribir", 20261016, None),
                        (8, "ini", "continua", 20261012, None),
                        (8, "fin", "continua", 20261016, None)]
    assert {a.motivo for a in plan.acciones if a.id == 8} == {
        "continúa (cadena de la incidencia 7)"}
    assert _r(plan) == [(7, "abre", 20261005, "cierra", 20261016, 7),
                        (8, "continua", 20261005, "cadena", 20261016, 7)]


def test_f062_c2_r14_decidir_alarga_el_ciz_propio_sin_insertar():
    lineas = [_l(51, 20261005, sk=SK_INI), _l(52, 20261009, "CIZ", sk=SK_FIN)]
    plan = _decidir(lineas, _inc(7, 5, 9, hmores_ide_ini=51, hmores_ide_fin=52,
                                 dia_ini=5, dia_fin=9), _inc(8, 12, 16))
    assert _v(plan)[:2] == [(7, "ini", "ya_registrado", 20261005, 51),
                            (7, "fin", "editar", 20261016, 52)]
    fin = plan.acciones[1]
    assert (fin.fec_antes, fin.synckey_leida, fin.can_leido, fin.ajena,
            fin.hmoide, fin.parte_cod) == (20261009, SK_FIN, 0.0, False, 100,
                                           "PT26/00100")


def test_f062_c2_decidir_dos_rachas_si_el_lunes_corta():
    lineas = [_l(51, 20261005, sk=SK_INI), _l(52, 20261009, "CIZ", sk=SK_FIN)]
    plan = _decidir(lineas, _inc(8, 13, 16))
    assert _v(plan) == [(8, "ini", "escribir", 20261013, None),
                        (8, "fin", "escribir", 20261016, None)]


def test_f062_c3_r7_decidir_a_fin_de_mes_queda_abierta():
    plan = _decidir([], _inc(7, 27, 31))
    assert _v(plan) == [(7, "ini", "escribir", 20261027, None),
                        (7, "fin", "abierta", 20261031, None)]
    assert _r(plan) == [(7, "abre", 20261027, "abierta", None, 7)]
    # C4 (D7): del 27 al 30, también (el 31 es sábado).
    assert [a.accion for a in _decidir([], _inc(7, 27, 30)).acciones] == [
        "escribir", "abierta"]


def test_f062_c3_r1b_r5_decidir_noviembre_sin_inicio_y_ciz_en_su_parte():
    civ = _l(51, 20261027, sk=SK_INI, parte="PT26/00100")
    plan = _decidir([civ], _inc(8, 2, 6, mes=11))
    assert _v(plan) == [(8, "ini", "continua", 20261102, None),
                        (8, "fin", "escribir", 20261106, None)]
    ini, fin = plan.acciones
    assert ini.motivo == ("continúa la racha CIV del 27/10 (parte PT26/00100, "
                          "línea 51)")
    assert fin.hmoide_destino is None    # el inicio no es de M: paso 5
    assert _r(plan) == [(8, "continua", 20261027, "cierra", 20261106, 8)]


def test_f062_c5_decidir_baja_de_septiembre_a_noviembre():
    cie = [_l(41, 20260915, "CIE", sk="porcentajes:inc:5:ini")]
    octubre = _decidir(cie, _inc(8, 1, 31, "CIE"))
    assert _v(octubre) == [(8, "ini", "continua", 20261001, None),
                           (8, "fin", "abierta", 20261031, None)]
    noviembre = _decidir(cie, _inc(9, 1, 10, "CIE", mes=11))
    assert _v(noviembre) == [(9, "ini", "continua", 20261101, None),
                             (9, "fin", "escribir", 20261110, None)]


def test_f062_c6_r3_r14_d12_decidir_continua_la_de_otra_obra_y_mueve_su_ciz():
    admin = [_l(61, 20261005, obride=40, hmoide=400, parte="PT26/00040"),
             _l(62, 20261007, "CIZ", obride=40, hmoide=400, parte="PT26/00040",
                can=1.0, sk=None)]
    plan = _decidir(admin, _inc(7, 5, 9, obra=60))
    assert _v(plan) == [(7, "ini", "continua", 20261005, None),
                        (7, "fin", "editar", 20261009, 62)]
    fin = plan.acciones[1]
    assert (fin.fec_antes, fin.synckey_leida, fin.can_leido, fin.ajena,
            fin.hmoide, fin.parte_cod, fin.hora_codigo) == (
        20261007, None, 1.0, True, 400, "PT26/00040", "CIZ")
    assert _r(plan) == [(7, "continua", 20261005, "cierra", 20261009, 7)]
    assert plan.resumenes[0].cierre_parte == "PT26/00040"


def test_f062_c9_r18_decidir_repetir_la_de_c6_no_mueve_nada():
    movido = [_l(61, 20261005, obride=40, hmoide=400),
              _l(62, 20261009, "CIZ", obride=40, hmoide=400, can=1.0)]
    plan = _decidir(movido, _inc(7, 5, 9, obra=60, hmores_ide_fin=62,
                                 dia_fin=9, dia_fin_antes=7))
    assert _v(plan) == [(7, "ini", "continua", 20261005, None),
                        (7, "fin", "ya_registrado", 20261009, 62)]
    assert plan.acciones[1].ajena is True


def test_f062_r16_decidir_si_ya_no_lo_continua_devuelve_el_ciz_ajeno():
    movido = [_l(61, 20261005, obride=40, hmoide=400),
              _l(62, 20261009, "CIZ", obride=40, hmoide=400, can=1.0)]
    # Ahora del 5 al 6: el CIZ ajeno, en su día original (7), la cubre.
    plan = _decidir(movido, _inc(7, 5, 6, obra=60, hmores_ide_fin=62,
                                 dia_fin=9, dia_fin_antes=7))
    assert _v(plan) == [(7, "ini", "continua", 20261005, None),
                        (7, "fin", "ya_registrado", 20261007, None),
                        (7, "devolver", "editar", 20261007, 62)]
    dev = plan.acciones[2]
    assert (dev.fec_antes, dev.can_leido, dev.ajena, dev.hora_codigo) == (
        20261009, 1.0, True, "CIZ")
    assert _r(plan) == [(7, "continua", 20261005, "cubierta", 20261007, 7)]


def test_f062_r16_decidir_devolver_a_un_parte_cerrado_se_omite():
    movido = [_l(61, 20261005), _l(62, 20261009, "CIZ", est=3,
                                     parte="PT26/00040")]
    plan = _decidir(movido, _inc(7, 5, 6, hmores_ide_fin=62, dia_fin=9,
                                 dia_fin_antes=7))
    dev = plan.acciones[2]
    assert (dev.rol, dev.accion, dev.motivo) == (
        "devolver", "omitir", ("el CIZ (línea 62) no se puede devolver al "
        "07/10: el parte PT26/00040 no está En registro"))


def test_f062_r4_decidir_un_ciz_ajeno_nunca_se_acorta():
    admin = [_l(61, 20261005), _l(62, 20261012, "CIZ", parte="PT26/00040")]
    plan = _decidir(admin, _inc(7, 5, 9))
    assert _v(plan) == [(7, "ini", "continua", 20261005, None),
                        (7, "fin", "ya_registrado", 20261012, None)]
    assert plan.acciones[1].motivo == (
        "la cierra el CIZ del 12/10 (parte PT26/00040, línea 62)")
    assert [a.accion for a in plan.acciones if a.rol == "devolver"] == []


def test_f062_r5_decidir_el_ciz_va_al_parte_del_inicio_si_es_de_m():
    civ = _l(61, 20261005, obride=40, hmoide=400, parte="PT26/00040",
             cenide=4001, paride=8040, caaide=9040, parte_emp=1)
    plan = _decidir([civ], _inc(7, 5, 9, obra=60))
    fin = plan.acciones[1]
    assert (fin.accion, fin.hmoide_destino, fin.obride, fin.cenide,
            fin.paride, fin.caa_ide, fin.parte_cod) == (
        "escribir", 400, 40, 4001, 8040, 9040, "PT26/00040")
    assert plan.resumenes[0].cierre_parte == "PT26/00040"


@pytest.mark.parametrize("cambio", [{"est": 3}, {"parte_emp": 2},
                                    {"obride": 41}])
def test_f062_r5_decidir_si_el_parte_del_inicio_no_vale_va_al_paso_5(cambio):
    datos = {"obride": 40, "hmoide": 400, "cenide": 4001, "parte_emp": 1}
    datos.update(cambio)
    civ = _l(61, 20261005, **datos)
    fin = _decidir([civ], _inc(7, 5, 9), pruebas=40).acciones[1]
    assert (fin.accion, fin.hmoide_destino) == ("escribir", None)


def test_f062_r9_c7_decidir_una_ajena_en_el_tramo_omite_la_cadena():
    otra = _l(61, 20261007, "CIE", parte="PT26/00041", sk="partes:3")
    plan = _decidir([otra], _inc(7, 5, 9), _inc(8, 12, 16))
    motivo = ("en el tramo ya está la línea 61 (CIE, 07/10) del parte "
              "PT26/00041, de partes: no se escribe ni se mueve nada")
    assert [(a.id, a.rol, a.accion, a.motivo) for a in plan.acciones] == [
        (7, "ini", "omitir", motivo), (7, "fin", "omitir", motivo),
        (8, "ini", "omitir", motivo), (8, "fin", "omitir", motivo)]
    assert plan.resumenes == []


@pytest.mark.parametrize("sk, origen", [
    (None, "de Administración"), ("porcentajes:inc:9:ini", "de la incidencia 9"),
    ("otro:1", "de otro sistema")])
def test_f062_r9_decidir_el_motivo_dice_de_quien_es(sk, origen):
    otra = _l(61, 20261006, "CIV", sk=sk)
    plan = _decidir([otra, _l(62, 20261008, "CIZ")], _inc(7, 5, 9))
    assert plan.acciones[0].motivo.endswith(
        f"{origen}: no se escribe ni se mueve nada")


def test_f062_r9_c7_decidir_codigos_distintos_no_se_estorban_fuera_del_tramo():
    # C7: la V del 5-9 ya escrita no estorba a la B del 12-16.
    v = [_l(51, 20261005, sk=SK_INI), _l(52, 20261009, "CIZ", sk=SK_FIN)]
    plan = _decidir(v, _inc(8, 12, 16, "CIB"))
    assert [a.accion for a in plan.acciones] == ["escribir", "escribir"]


def test_f062_r11_decidir_con_inicio_propio_no_se_une_y_avisa():
    lineas = [_l(41, 20261001), _l(51, 20261006, sk=SK_INI)]
    plan = _decidir(lineas, _inc(7, 5, 9, hmores_ide_ini=51, dia_ini=6))
    assert _v(plan) == [(7, "ini", "editar", 20261005, 51),
                        (7, "fin", "escribir", 20261009, None)]
    assert plan.acciones[0].fec_antes == 20261006
    assert plan.acciones[1].hmoide_destino == 100     # el parte del inicio
    assert plan.resumenes[0].papel == "abre"
    assert plan.resumenes[0].avisos == [
        ("no se une a la racha CIV del 01/10 (parte PT26/00100): su inicio "
        "(línea 51) ya está escrito")]


def test_f062_r11_decidir_un_ciz_propio_a_fin_de_mes_va_al_ultimo_dia():
    lineas = [_l(51, 20261020, sk=SK_INI), _l(52, 20261023, "CIZ", sk=SK_FIN)]
    plan = _decidir(lineas, _inc(7, 20, 30, hmores_ide_ini=51,
                                 hmores_ide_fin=52, dia_ini=20, dia_fin=23))
    assert _v(plan) == [(7, "ini", "ya_registrado", 20261020, 51),
                        (7, "fin", "editar", 20261031, 52)]
    assert plan.resumenes[0].avisos == [
        ("no se deja abierta: el CIZ (línea 52) ya está en el mes; va al "
        "último día")]
    assert _r(plan) == [(7, "abre", 20261020, "cierra", 20261031, 7)]


def test_f062_r11_decidir_el_ciz_de_la_previa_a_fin_de_mes_va_al_ultimo_dia():
    admin = [_l(61, 20261019), _l(62, 20261021, "CIZ")]
    plan = _decidir(admin, _inc(7, 19, 30))
    assert _v(plan) == [(7, "ini", "continua", 20261019, None),
                        (7, "fin", "editar", 20261031, 62)]
    assert plan.acciones[1].ajena is True


def test_f062_r21_decidir_con_ciz_en_m1_no_escribe_y_avisa():
    lineas = [_l(51, 20261027, sk=SK_INI),
              _l(70, 20261106, "CIZ", sk="porcentajes:inc:8:fin",
                 parte="PT26/00111")]
    plan = _decidir(lineas, _inc(7, 27, 29, hmores_ide_ini=51, dia_ini=27))
    assert _v(plan) == [(7, "ini", "ya_registrado", 20261027, 51),
                        (7, "fin", "abierta", 20261029, None)]
    aviso = ("la racha sigue en 11/2026: su CIZ (línea 70) es del 06/11 en "
             "el parte PT26/00111; no se escribe el CIZ")
    assert plan.acciones[1].motivo == aviso
    assert plan.resumenes[0].avisos == [aviso]
    # Con la previa de otro (abierta en M y cerrada en M+1), igual.
    lineas[0] = _l(51, 20261027, sk=None)
    plan = _decidir(lineas, _inc(7, 27, 29))
    assert [a.accion for a in plan.acciones] == ["continua", "abierta"]


def test_f062_r10_decidir_abre_otra_y_lleva_el_aviso():
    lineas = [_l(1, 20260920), _l(2, 20260930, "CIZ", parte="PT26/00090")]
    plan = _decidir(lineas, _inc(7, 1, 9))
    assert [a.accion for a in plan.acciones] == ["escribir", "escribir"]
    assert plan.resumenes[0].avisos == [
        ("la racha CIV del 20/09 se cerró el 30/09 en el parte PT26/00090 "
        "(línea 2), del mes anterior: se abre otra")]


def test_f062_r14_decidir_inicio_propio_cambiado_a_mano_o_en_parte_cerrado():
    cambiado = [_l(51, 20261006, sk=SK_INI, can=1.0)]
    plan = _decidir(cambiado, _inc(7, 5, 9, hmores_ide_ini=51, dia_ini=6))
    assert (plan.acciones[0].accion, plan.acciones[0].motivo) == (
        "omitir", MOTIVO_INC_CAMBIADA.format(ide=51))
    cerrado = [_l(51, 20261006, sk=SK_INI, est=3, parte="PT26/7"),
               _l(52, 20261009, "CIZ", sk=SK_FIN, est=3, parte="PT26/7")]
    plan = _decidir(cerrado, _inc(7, 5, 9, hmores_ide_ini=51, dia_ini=6,
                                  hmores_ide_fin=52, dia_fin=9))
    assert [(a.rol, a.accion, a.motivo) for a in plan.acciones] == [
        ("ini", "omitir", "el parte PT26/7 está cerrado: sigue del 6 al 9"),
        ("fin", "ya_registrado", ("ya registrada en Sigrid (línea 52); no se "
                                 "duplica"))]


def test_f062_r26_decidir_si_la_base_omite_se_omite_la_cadena():
    [c] = cadenas([_inc(7, 5, 9, "CIX"), _inc(8, 12, 16, "CIX")])
    base = decidir_incidencia(c.duena, HORAS)
    plan = decidir_cadena(c, [], base, est=EST, empresa=1)
    assert [(a.id, a.accion) for a in plan.acciones] == [
        (7, "omitir"), (7, "omitir"), (8, "omitir"), (8, "omitir")]
    assert {a.motivo for a in plan.acciones} == {base[0].motivo}
    assert plan.resumenes == []


def test_f062_r6_decidir_lo_escrito_lleva_la_base_de_la_duena():
    plan = _decidir([], _inc(7, 5, 9, paride=80001), _inc(8, 12, 16))
    ini, fin = plan.acciones[:2]
    assert (ini.hora_ide, ini.pre, fin.hora_ide, fin.paride) == (
        71, 12.5, 79, 80001)


# ================ T5: cierres del mes anterior (R12, R13, D14) ============ #
from application.services.rachas import (
    cierres_mes_anterior,
    obras_de_cierres,
    origen_de,
)
from domain.models.registro_models import ParteSigrid

#: El inicio, con su obra, centro, partida y cuenta (E-6, E-13).
INICIO = {"obride": 40, "cenide": 7, "paride": 300, "caaide": 400}


def _cierres(lineas, incs=(), partes=None, mes=11, est=EST, empresa=1,
             pruebas=None, recurso=200):
    """Los cierres al registrar `mes` de 2026 del recurso 200."""
    return cierres_mes_anterior(
        emparejar(lineas), recurso, list(incs), partes or {}, 2026, mes,
        est=est, empresa=empresa, obride_pruebas=pruebas)


def _c(cierre):
    return (cierre.accion, cierre.fecha_int, cierre.parte_cod, cierre.hmoide,
            cierre.synckey, cierre.incidencia_id)


def test_f062_c4_cierres_inicio_de_m1_sin_continuacion_cierra_en_su_parte():
    lineas = [_l(51, 20261027, sk="porcentajes:inc:5:ini", **INICIO)]
    [c] = _cierres(lineas)
    assert _c(c) == ("escribir", 20261031, "PT26/00100", 100,
                     "porcentajes:inc:5:fin", 5)
    assert (c.recurso_ide, c.codigo, c.inicio_ide, c.inicio_fec,
            c.inicio_parte) == (200, "CIV", 51, 20261027, "PT26/00100")
    assert (c.obride, c.cenide, c.paride, c.caaide) == (40, 7, 300, 400)
    assert c.motivo == ("la racha CIV del 27/10 (parte PT26/00100) no sigue "
                        "en 11/2026: CIZ el 31/10 en el parte PT26/00100")


@pytest.mark.parametrize("kw", [{"est": 3}, {"parte_emp": 2},
                                {"obride": 41}])
def test_f062_r13_cierres_parte_del_inicio_que_no_vale_solo_avisa(kw):
    datos = {**INICIO, **kw}
    lineas = [_l(51, 20261027, sk="porcentajes:inc:5:ini", **datos)]
    [c] = _cierres(lineas, pruebas=40)
    assert (c.accion, c.fecha_int, c.hmoide) == ("aviso", 20261031, None)
    assert c.motivo == ("la racha CIV del 27/10 (parte PT26/00100) no sigue "
                        "en 11/2026 y no se puede cerrar el 31/10: el parte "
                        "PT26/00100 no está En registro, no es de la empresa "
                        "o no es de la obra de pruebas")


def test_f062_c5_cierres_la_que_continua_una_incidencia_de_m_no_se_cierra():
    lineas = [_l(51, 20260915, "CIE", sk="porcentajes:inc:3:ini", **INICIO)]
    octubre = _inc(9, 1, 31, "CIE", mes=10)
    assert _cierres(lineas, [octubre], mes=10) == []
    noviembre = _inc(10, 1, 10, "CIE", mes=11)
    assert _cierres(lineas, [noviembre]) == []
    # Otro código o no pegada al último día de M−1: no la continúa.
    assert len(_cierres(lineas, [_inc(10, 1, 10, "CIV", mes=11)])) == 1
    assert len(_cierres(lineas, [_inc(10, 3, 10, "CIE", mes=11)])) == 1


def test_f062_c12_cierres_inicio_anterior_a_m1_en_el_parte_de_m1_de_su_obra():
    lineas = [_l(51, 20260915, "CIE", sk="porcentajes:inc:3:ini",
                 parte="PT26/00090", hmoide=90, **INICIO)]
    partes = {(40, 2026, 10): [ParteSigrid(130, "PT26/00130", 3),
                               ParteSigrid(120, "PT26/00120", EST),
                               ParteSigrid(110, "PT26/00110", EST)]}
    [c] = _cierres(lineas, partes=partes)
    assert _c(c) == ("escribir", 20261031, "PT26/00120", 120,
                     "porcentajes:inc:3:fin", 3)
    assert (c.obride, c.cenide, c.paride, c.caaide) == (40, 7, 300, 400)
    assert c.motivo == ("la racha CIE del 15/09 (parte PT26/00090) no sigue "
                        "en 11/2026: CIZ el 31/10 en el parte PT26/00120")
    assert obras_de_cierres(emparejar(lineas), 200, [], 2026, 11,
                            est=EST) == {40}


@pytest.mark.parametrize("partes", [
    {}, {(40, 2026, 10): []}, {(40, 2026, 10): [ParteSigrid(130, "X", 3)]},
    {(41, 2026, 10): [ParteSigrid(120, "PT26/00120", 1)]}])
def test_f062_c12_cierres_sin_parte_de_m1_que_valga_solo_avisa(partes):
    lineas = [_l(51, 20260915, "CIE", sk="porcentajes:inc:3:ini",
                 parte="PT26/00090", **INICIO)]
    [c] = _cierres(lineas, partes=partes)
    assert (c.accion, c.hmoide, c.parte_cod) == ("aviso", None, None)
    assert c.motivo == ("la racha CIE del 15/09 (parte PT26/00090) no sigue "
                        "en 11/2026 y no se puede cerrar el 31/10: su obra no "
                        "tiene en 10/2026 ningún parte En registro")


def test_f062_c12_cierres_d14_de_otra_empresa_o_fuera_de_pruebas_avisa():
    partes = {(40, 2026, 10): [ParteSigrid(120, "PT26/00120", EST)]}
    for kw, pruebas in (({"parte_emp": 2}, None), ({}, 41)):
        lineas = [_l(51, 20260915, "CIE", sk="porcentajes:inc:3:ini",
                     **{**INICIO, **kw})]
        [c] = _cierres(lineas, partes=partes, pruebas=pruebas)
        assert c.accion == "aviso"


def test_f062_r12_cierres_inicio_ajeno_lleva_synckey_de_cierre():
    lineas = [_l(51, 20261027, sk=None, **INICIO)]
    [c] = _cierres(lineas)
    assert _c(c) == ("escribir", 20261031, "PT26/00100", 100,
                     "porcentajes:inc:cierre:51", None)
    lineas = [_l(51, 20261027, sk="partes:9:1", **INICIO)]
    assert _c(_cierres(lineas)[0])[4] == "porcentajes:inc:cierre:51"


def test_f062_r18_cierres_ya_cerrada_el_ultimo_dia_con_nuestra_synckey():
    for sk_ini, sk_fin in (("porcentajes:inc:5:ini", "porcentajes:inc:5:fin"),
                           (None, "porcentajes:inc:cierre:51")):
        lineas = [_l(51, 20261027, sk=sk_ini, **INICIO),
                  _l(52, 20261031, "CIZ", sk=sk_fin, parte="PT26/00101",
                     hmoide=101)]
        [c] = _cierres(lineas)
        assert _c(c)[:4] == ("ya_registrado", 20261031, "PT26/00101", 101)
        assert c.hmores_ide == 52
    # Cerrada por otro el último día, o antes: no es un cierre nuestro.
    for ciz in (_l(52, 20261031, "CIZ"),
                _l(52, 20261030, "CIZ", sk="porcentajes:inc:5:fin")):
        lineas = [_l(51, 20261027, sk="porcentajes:inc:5:ini"), ciz]
        assert _cierres(lineas) == []


def test_f062_r12_cierres_solo_las_abiertas_de_antes_de_m_del_recurso():
    # Inicio en M (abierta en noviembre), otro recurso, cerrada en M.
    assert _cierres([_l(51, 20261103, **INICIO)]) == []
    assert _cierres([_l(51, 20261027, reside=201, **INICIO)]) == []
    assert _cierres([_l(51, 20261027, **INICIO),
                     _l(52, 20261104, "CIZ")]) == []
    assert obras_de_cierres(emparejar([_l(51, 20261027, **INICIO)]), 200,
                            [], 2026, 11, est=EST) == set()


def test_f062_r12_cierres_en_enero_cierra_el_31_de_diciembre():
    lineas = [_l(51, 20251229, sk="porcentajes:inc:5:ini", **INICIO)]
    [c] = cierres_mes_anterior(emparejar(lineas), 200, [], {}, 2026, 1,
                               est=EST, empresa=1)
    assert (c.accion, c.fecha_int) == ("escribir", 20251231)


def test_f062_r9_cierres_origen_de_una_synckey_de_cierre():
    assert origen_de(_l(1, 20261005, sk="porcentajes:inc:cierre:51")) == (
        "de un cierre de racha de porcentajes")


# ============= T5b: «no coincide con Sigrid» (R17, R30, D15, D16) ========= #
from application.services.rachas import no_coincide

MOTIVO_QUITADA = "quitada en la plataforma; sigue en Sigrid"
MOTIVO_SOLO_SIGRID = "en Sigrid y no en la plataforma"


def _nc(lineas, quitadas=(), incs=(), previas=(), designado=True):
    """«No coincide» del recurso 200 al registrar octubre de 2026."""
    return no_coincide(lineas, 200, list(quitadas), list(incs), set(previas),
                       2026, 10, designado=designado)


def _vista(nc):
    return (nc.tipo, nc.recurso_ide, nc.incidencia_id,
            [(x.ide, x.codigo, x.fecha_int, x.parte_cod) for x in nc.lineas],
            nc.motivo, nc.en_sigrid)


def test_f062_c10_no_coincide_quitada_con_sus_lineas_en_sigrid():
    quitada = _inc(7, 5, 9, hmores_ide_ini=51, dia_ini=5, hmores_ide_fin=52,
                   dia_fin=9)
    lineas = [_l(51, 20261005, sk=SK_INI), _l(52, 20261009, "CIZ", sk=SK_FIN)]
    assert [_vista(x) for x in _nc(lineas, [quitada])] == [
        ("quitada", 200, 7, [(51, "CIV", 20261005, "PT26/00100"),
                             (52, "CIZ", 20261009, "PT26/00100")],
         MOTIVO_QUITADA, [51, 52])]
    # Sin designar también: la quitada viaja en la petición de su obra.
    assert len(_nc(lineas, [quitada], designado=False)) == 1


def test_f062_c10_no_coincide_quitada_borrada_a_mano_sin_lineas_ni_aviso():
    quitada = _inc(7, 5, 9, hmores_ide_ini=51, dia_ini=5, hmores_ide_fin=52,
                   dia_fin=9)
    [nc] = _nc([], [quitada])
    assert (nc.tipo, nc.incidencia_id, nc.lineas, nc.en_sigrid) == (
        "quitada", 7, [], [])
    # Solo una de las dos sigue: esa.
    [nc] = _nc([_l(52, 20261009, "CIZ", sk=SK_FIN)], [quitada])
    assert [x.ide for x in nc.lineas] == nc.en_sigrid == [52]


def test_f062_c9_no_coincide_quitada_que_movio_un_ciz_ajeno_no_lo_lista():
    # C6 quitada: continuó la racha de Administración (61, 62) y movió su
    # CIZ del 7 al 9; el CIZ se devuelve (R16) y no sale, ni la racha.
    quitada = _inc(7, 5, 9, obra=60, hmores_ide_fin=62, dia_fin=9,
                   dia_fin_antes=7)
    lineas = [_l(61, 20261005, parte="PT26/00040"),
              _l(62, 20261009, "CIZ", parte="PT26/00040")]
    [nc] = _nc(lineas, [quitada])
    assert (nc.tipo, nc.lineas, nc.en_sigrid) == ("quitada", [], [])


def test_f062_c11_no_coincide_solo_en_sigrid_por_racha_y_solo_designados():
    lineas = [_l(61, 20261020, "CIE", parte="PT26/00040"),
              _l(62, 20261022, "CIZ", parte="PT26/00040"),
              _l(63, 20261026, "CIB", parte="PT26/00040")]
    assert [_vista(x) for x in _nc(lineas)] == [
        ("solo_sigrid", 200, None, [(61, "CIE", 20261020, "PT26/00040"),
                                    (62, "CIZ", 20261022, "PT26/00040")],
         MOTIVO_SOLO_SIGRID, []),
        ("solo_sigrid", 200, None, [(63, "CIB", 20261026, "PT26/00040")],
         MOTIVO_SOLO_SIGRID, [])]
    assert _nc(lineas, designado=False) == []


def test_f062_c11_no_coincide_lo_que_explica_una_incidencia_no_sale():
    # C6: la previa de Administración que la incidencia continúa.
    previa_adm = [_l(61, 20261005, parte="PT26/00040"),
                  _l(62, 20261007, "CIZ", parte="PT26/00040")]
    assert _nc(previa_adm, incs=[_inc(7, 5, 9, obra=60)],
               previas={61, 62}) == []
    # Una racha con una línea propia (por synckey o por traza) no sale.
    propia = [_l(51, 20261005, sk=SK_INI), _l(62, 20261012, "CIZ")]
    assert _nc(propia, incs=[_inc(7, 5, 9)]) == []
    # La propia de una quitada tampoco sale como «solo en Sigrid».
    quitada = _inc(7, 5, 9, hmores_ide_ini=51, dia_ini=5)
    assert [x.tipo for x in _nc(propia, [quitada])] == ["quitada"]


def test_f062_r30_no_coincide_solo_lineas_del_mes_y_del_recurso():
    lineas = [_l(61, 20260915, "CIE"), _l(62, 20261007, "CIZ"),
              _l(63, 20261028, "CIV"), _l(64, 20261104, "CIZ"),
              _l(65, 20261012, "CIV", reside=201),
              _l(66, 20261014, "CIZ")]
    assert [[x.ide for x in nc.lineas] for nc in _nc(lineas)] == [
        [62], [66], [63]]


def test_f062_r30_decidir_dice_que_lineas_son_de_la_previa():
    adm = [_l(61, 20261005, parte="PT26/00040"),
           _l(62, 20261007, "CIZ", parte="PT26/00040")]
    assert _decidir(adm, _inc(7, 5, 9, obra=60)).previas == {61, 62}
    assert _decidir([], _inc(7, 5, 9)).previas == set()
    abierta = [_l(61, 20261001, parte="PT26/00040")]
    assert _decidir(abierta, _inc(7, 5, 9)).previas == {61}
