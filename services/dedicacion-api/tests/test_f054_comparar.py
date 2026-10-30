# tests/test_f054_comparar.py
"""F-054 · T4: el dominio puro de traer de Sigrid (`domain/traer_sigrid.py`;
R13-R18, design §5.1).

- R13: por trabajador y entrada; normal = la obra, postventa = (obra de
  origen, postventa), VAR = `obra.ide` −`var_paride`.
- R14: a `no_traidas`, con su motivo, la línea de un trabajador no visible
  o no vigente, la de una entrada que no está en la base, es de otra
  empresa o no se ofrece, y la que trae motivo del transfer; la de un
  recurso de `recurso_vinculado` (una `MESVE`) solo cuenta en
  `de_vinculados`; las demás de recursos fuera del maestro, solo
  `fuera_maestro`.
- R15: se suman; con partidas distintas (normal), `no_traducible`.
- R16: % = suma × 100 a centésimas; ≤ 0 o > 100, `no_traducible`.
- R17: normal, su partida como elegida (0 = automática); postventa,
  automática; VAR, la fija (ninguna elegida).
- R18: los cinco estados; épsilon 0,005 en los dos bordes; la partida no
  cuenta. El menor `hmores_ide`.

Sin red ni BBDD.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from domain.models import FiltroEmpresa, Linea, LineaSigridTraida, Obra, Trabajador
from domain.traer_sigrid import (
    MOTIVO_NO_EN_BASE,
    MOTIVO_NO_OFRECIBLE,
    MOTIVO_NO_VIGENTE,
    MOTIVO_NO_VISIBLE,
    MOTIVO_OTRA_EMPRESA,
    MOTIVO_PARTIDAS_DISTINTAS,
    MOTIVO_PORCENTAJE_FUERA,
    EntradaSigrid,
    EstadoEntrada,
    a_linea,
    comparar,
    entradas_por_trabajador,
)

FILTRO = FiltroEmpresa(empresa=1, por_defecto=1, empresa_obras=1)


def _o(ide, *, empresa=1, activa=True, pv=False) -> Obra:
    return Obra(ide=ide, cod=f"{ide:04d}" if ide > 0 else f"VAR-{-ide}",
                descripcion=f"OBRA {ide}", estado_sigrid=None, activa=activa,
                empresa=empresa, admite_postventa=pv)


OBRAS = {o.ide: o for o in [
    _o(694), _o(678, pv=True), _o(700, activa=False, pv=True),
    _o(701, activa=False), _o(900, empresa=28), _o(-417055)]}


def _t(ide, empresa=1, activo=True, baja=None) -> Trabajador:
    return Trabajador(ide=ide, cod=str(ide), nombre=f"T{ide}", dni=None,
                      categoria=None, activo=activo, empresa=empresa,
                      fecha_baja=baja)


TRABAJADORES = {t.ide: t for t in [
    _t(10), _t(11, empresa=28), _t(12, activo=False),
    _t(13, baja=20260815), _t(14, baja=20260901)]}


def _s(ide, recurso=10, obra=694, *, can=0.5, destino="normal", paride=0,
       origen=None, var=None, motivo=None, parte="PT26/00001",
       partida_cod=None) -> LineaSigridTraida:
    return LineaSigridTraida(
        hmores_ide=ide, recurso_ide=recurso, obra_ide=obra,
        obra_cod=f"{obra:04d}", parte_ide=7000, parte_cod=parte,
        parte_est=1, en_registro=True, hora="MENC", can=can, fec=20260930,
        paride=paride, partida_cod=partida_cod, partida_res=None,
        synckey=None, destino=destino, obra_origen_ide=origen,
        var_paride=var, motivo=motivo)


def _entradas(lineas, vinculados=frozenset()):
    return entradas_por_trabajador(
        lineas, OBRAS, filtro=FILTRO, anio=2026, mes=9,
        trabajadores=TRABAJADORES, vinculados=set(vinculados))


def _ln(obra, pct, pv=False, partida=None) -> Linea:
    return Linea(obra_ide=obra, es_postventa=pv, porcentaje=Decimal(pct),
                 partida_ide=partida)


# ======================= R13 · las tres entradas ======================== #
def test_f054_r13_normal_postventa_y_var():
    por, no, cont = _entradas([
        _s(5, obra=694, can=0.4, paride=2105, partida_cod="CI.1"),
        _s(3, obra=999001, can=0.1, destino="postventa", paride=70001,
           origen=678),
        _s(4, obra=683806, can=0.5, destino="var", paride=417055,
           var=417055)])
    assert no == [] and (cont.fuera_maestro, cont.de_vinculados) == (0, 0)
    assert [(e.obra_ide, e.es_postventa, e.porcentaje) for e in por[10]] == [
        (-417055, False, Decimal("50.00")), (678, True, Decimal("10.00")),
        (694, False, Decimal("40.00"))]


# ============================ R14 · motivos ============================= #
@pytest.mark.parametrize("linea, motivo", [
    (_s(1, recurso=11), MOTIVO_NO_VISIBLE.format(empresa=1)),
    (_s(1, recurso=12), MOTIVO_NO_VIGENTE.format(mes=9, anio=2026)),
    (_s(1, recurso=13), MOTIVO_NO_VIGENTE.format(mes=9, anio=2026)),
    (_s(1, obra=555), MOTIVO_NO_EN_BASE.format(obra="0555")),
    (_s(1, obra=900), MOTIVO_OTRA_EMPRESA.format(obra="0900", emp=28,
                                                 empresa=1)),
    (_s(1, obra=701), MOTIVO_NO_OFRECIBLE.format(obra="0701",
                                                 modo="normal")),
    (_s(1, obra=999001, destino="postventa", origen=694),
     MOTIVO_NO_OFRECIBLE.format(obra="0694", modo="en postventa")),
    (_s(1, obra=683806, destino="var", var=1234),
     MOTIVO_NO_EN_BASE.format(obra="VAR-1234")),
    (_s(1, motivo="la partida 0 de POSTV2 no casa"),
     "la partida 0 de POSTV2 no casa"),
])
def test_f054_r14_cada_motivo_va_a_no_traidas(linea, motivo):
    por, no, cont = _entradas([linea])
    assert por == {}
    assert [(n.hmores_ide, n.recurso_ide, n.motivo) for n in no] == [
        (1, linea.recurso_ide, motivo)]
    assert (no[0].obra_cod, no[0].parte_cod, no[0].can) == (
        linea.obra_cod, "PT26/00001", linea.can)
    assert (cont.fuera_maestro, cont.de_vinculados) == (0, 0)


def test_f054_r14_baja_en_el_mes_sigue_vigente():
    por, no, _ = _entradas([_s(1, recurso=14)])
    assert no == [] and list(por) == [14]


def test_f054_r14_postventa_en_obra_que_la_admite_aunque_no_activa():
    por, no, _ = _entradas([_s(1, obra=999001, destino="postventa",
                               origen=700)])
    assert no == [] and por[10][0].clave() == (700, True)


def test_f054_r14_fuera_del_maestro_solo_se_cuenta():
    por, no, cont = _entradas([_s(1, recurso=77), _s(2, recurso=77),
                               _s(3, recurso=78)])
    assert (por, no) == ({}, [])
    assert (cont.fuera_maestro, cont.de_vinculados) == (3, 0)


def test_f054_r14_d18_la_mesve_de_un_vinculado_solo_en_de_vinculados():
    """Una `MESVE` de un recurso de `recurso_vinculado` (activo o no): ni
    entrada ni no traída ni fuera del maestro, aunque su recurso fuera
    también un trabajador."""
    por, no, cont = _entradas([_s(1, recurso=5000), _s(2, recurso=5001),
                               _s(3, recurso=10)],
                              vinculados={5000, 5001, 10})
    assert (por, no) == ({}, [])
    assert (cont.fuera_maestro, cont.de_vinculados) == (0, 3)


# =============================== R15 ==================================== #
def test_f054_r15_se_suman_y_el_menor_hmores_ide():
    por, _, _ = _entradas([_s(9, can=0.3, paride=5, parte="PT26/9"),
                           _s(4, can=0.25, paride=5, parte="PT26/4")])
    [e] = por[10]
    assert (e.porcentaje, e.n_lineas, e.hmores_ide, e.parte_cod) == (
        Decimal("55.00"), 2, 4, "PT26/4")
    assert e.motivo is None


def test_f054_r15_partidas_distintas_no_traducible():
    por, _, _ = _entradas([_s(1, paride=5), _s(2, paride=6)])
    [e] = por[10]
    assert e.motivo == MOTIVO_PARTIDAS_DISTINTAS
    [c] = comparar([], por[10])
    assert c.estado is EstadoEntrada.NO_TRADUCIBLE


def test_f054_r15_partida_y_sin_partida_tambien_distintas():
    por, _, _ = _entradas([_s(1, paride=5), _s(2, paride=0)])
    assert por[10][0].motivo == MOTIVO_PARTIDAS_DISTINTAS


def test_f054_r15_postventa_con_partidas_iguales_se_suma():
    por, _, _ = _entradas([
        _s(1, obra=999001, can=0.1, destino="postventa", paride=7, origen=678),
        _s(2, obra=999001, can=0.2, destino="postventa", paride=7,
           origen=678)])
    assert por[10][0].porcentaje == Decimal("30.00")


# =============================== R16 ==================================== #
@pytest.mark.parametrize("cans, pct, valida", [
    ([0.333333], "33.33", True), ([0.123456], "12.35", True),
    ([0.00004], "0.00", False), ([0.5, -0.5], "0.00", False),
    ([-0.1], "-10.00", False), ([1.0], "100.00", True),
    ([0.6, 0.40001], "100.00", True), ([0.6, 0.4001], "100.01", False),
])
def test_f054_r16_centesimas_y_rango(cans, pct, valida):
    por, _, _ = _entradas([_s(i + 1, can=c) for i, c in enumerate(cans)])
    [e] = por[10]
    assert e.porcentaje == Decimal(pct)
    assert (e.motivo is None) is valida
    if not valida:
        assert e.motivo == MOTIVO_PORCENTAJE_FUERA.format(pct=Decimal(pct))


# =============================== R17 ==================================== #
def test_f054_r17_normal_con_su_partida_como_elegida():
    por, _, _ = _entradas([_s(1, paride=2105, partida_cod="CI.1.5")])
    ln = a_linea(por[10][0], OBRAS[694])
    assert (ln.partida_ide, ln.partida_cod) == (2105, "CI.1.5")
    assert (ln.obra_ide, ln.es_postventa, ln.porcentaje) == (
        694, False, Decimal("50.00"))
    assert (ln.cod, ln.obra_activa, ln.obra_empresa) == ("0694", True, 1)
    assert ln.propuesta_ide is None and not ln.partida_fija


def test_f054_r17_normal_sin_partida_automatica():
    por, _, _ = _entradas([_s(1, paride=0)])
    ln = a_linea(por[10][0], OBRAS[694])
    assert (ln.partida_ide, ln.partida_cod, ln.partida_res) == (None,) * 3


def test_f054_r17_postventa_automatica_y_var_fija():
    por, _, _ = _entradas([
        _s(1, obra=999001, destino="postventa", paride=70001, origen=678),
        _s(2, obra=683806, destino="var", paride=417055, var=417055)])
    pv, var = sorted(por[10], key=lambda e: e.obra_ide, reverse=True)
    assert a_linea(pv, OBRAS[678]).partida_ide is None
    assert a_linea(pv, OBRAS[678]).es_postventa
    lv = a_linea(var, OBRAS[-417055])
    assert lv.partida_ide is None and lv.partida_fija


# =============================== R18 ==================================== #
def _e(obra, pct, pv=False, motivo=None, partida=None) -> EntradaSigrid:
    return EntradaSigrid(obra_ide=obra, es_postventa=pv,
                         porcentaje=Decimal(pct), partida_ide=partida,
                         hmores_ide=1, parte_cod="PT", n_lineas=1,
                         motivo=motivo)


def test_f054_r18_los_cinco_estados():
    cuadrante = [_ln(1, "40"), _ln(2, "30"), _ln(4, "30"), _ln(5, "10")]
    sigrid = [_e(1, "40"), _e(2, "35"), _e(3, "20"),
              _e(5, "10", motivo="x")]
    out = {(c.obra_ide, c.es_postventa): c for c in comparar(cuadrante,
                                                             sigrid)}
    assert {k: c.estado for k, c in out.items()} == {
        (1, False): EstadoEntrada.IGUAL, (2, False): EstadoEntrada.DISTINTA,
        (3, False): EstadoEntrada.SOLO_SIGRID,
        (4, False): EstadoEntrada.SOLO_CUADRANTE,
        (5, False): EstadoEntrada.NO_TRADUCIBLE}
    assert (out[(2, False)].pct_sigrid, out[(2, False)].pct_cuadrante) == (
        Decimal(35), Decimal(30))
    assert out[(3, False)].pct_cuadrante is None
    assert out[(4, False)].pct_sigrid is None and out[(4, False)].entrada \
        is None
    assert out[(5, False)].motivo == "x"
    assert [c.obra_ide for c in comparar(cuadrante, sigrid)] == [1, 2, 3, 4,
                                                                 5]


@pytest.mark.parametrize("sigrid, estado", [
    ("40.005", EstadoEntrada.IGUAL), ("39.995", EstadoEntrada.IGUAL),
    ("40.006", EstadoEntrada.DISTINTA), ("39.994", EstadoEntrada.DISTINTA)])
def test_f054_r18_epsilon_en_los_dos_bordes(sigrid, estado):
    [c] = comparar([_ln(1, "40")], [_e(1, sigrid)])
    assert c.estado is estado


def test_f054_r18_la_partida_no_cuenta_y_el_modo_si():
    [c] = comparar([_ln(1, "40", partida=9)], [_e(1, "40", partida=5)])
    assert c.estado is EstadoEntrada.IGUAL
    out = comparar([_ln(1, "40")], [_e(1, "40", pv=True)])
    assert [(c.es_postventa, c.estado) for c in out] == [
        (False, EstadoEntrada.SOLO_CUADRANTE),
        (True, EstadoEntrada.SOLO_SIGRID)]


def test_f054_r18_el_estado_es_texto():
    assert [e.value for e in EstadoEntrada] == [
        "igual", "distinta", "solo_sigrid", "solo_cuadrante",
        "no_traducible"]
