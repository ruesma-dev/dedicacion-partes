# tests/test_f068_reglas.py
"""F-068 · la partida del vinculado como la del trabajador, reglas puras
(`application/services/reglas_vinculados.py`; design §6.1).

- R5-R8 (T2): las piezas: las hojas activas con su cuenta
  (`hojas_con_subcuenta`), el capítulo CI.4 por número (`es_capitulo_ci4`),
  la puntuación del casador una a una (`puntuar`) y el desempate por el
  capítulo CI.4 (`desempate_ci4`).
- R4-R9 (T3): `partida_por_cuenta_o_nombre`: una con su cuenta ⇒
  `ci_tipo`; varias ⇒ el nombre y, en empate (también a 0), el CI.4; ninguna
  ⇒ el nombre entre las `CI*` que casan y, en empate, el CI.4; si no, sin
  partida con `sin_ci`, `varias_ci` o `empate_nombre`.
- R1-R3, R10 (T4): el historial del vinculado en la obra (`partida_por_
  historial`, sobre `previa_en_obra` del trabajador) va antes que la cuenta
  y el nombre; `partida_del_vinculado` sigue el orden elegida → titular →
  historial → cuenta y nombre → sin partida, sin leer nada.

Fixture «de la 0678» con `ide` inventados: cada cuenta de los vinculados
(`CICO13`, `CICO01`, `CICO15`, `CIMP09`) en dos hojas, una del capítulo
`CI.0` (o `CI.03P`) y otra del `CI.4`, con la misma descripción. Sin red ni
BBDD.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest
from application.services import propuesta_partida
from application.services import reglas_vinculados as rv
from application.services.partida_resolver import construir_catalogo
from application.services.propuesta_partida import LineaHistorial
from application.services.reglas_vinculados import (
    AVISO_SIN_PARTIDA_VINCULADO,
    METODO_CAPITULO_CI4,
    METODO_CI_TIPO,
    METODO_MANUAL,
    METODO_PARTE_ANTERIOR,
    METODO_TITULAR,
    MOTIVO_ELEGIDA_NO_VALIDA,
    MOTIVO_EMPATE_NOMBRE,
    MOTIVO_SIN_CI,
    MOTIVO_VARIAS_CI,
    PartidaElegida,
    PartidaTitular,
    PartidaVinculado,
    desempate_ci4,
    es_capitulo_ci4,
    hojas_con_subcuenta,
    partida_del_vinculado,
    partida_por_cuenta_o_nombre,
    partida_por_historial,
    por_que_sin_ci,
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
    _fila(60801, 60800, 1, "CP.1", "SEGUROS DECENALES"),
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


# ============================== R4-R9 (T3) =============================== #
def _pcn(sub, tipo_res=None, descripcion=None, cuentas=None):
    return partida_por_cuenta_o_nombre(
        _hojas(), CUENTAS if cuentas is None else cuentas, sub, tipo_res,
        descripcion)


def _e(ide: int) -> PartidaElegida:
    n = _hojas()[ide]
    return PartidaElegida(paride=ide, cod=n.cod, res=n.res)


def test_f068_r4_una_sola_hoja_con_su_cuenta_es_ci_tipo():
    """Aunque el nombre casara con otra: con UNA, esa (F-044 R15)."""
    assert _pcn("CIMO01") == (_e(60501), METODO_CI_TIPO)
    assert _pcn("CIMO01", "TELEFONO", "TELEFONO MOVIL 600") == (
        _e(60501), METODO_CI_TIPO)


def test_f068_r5_varias_con_su_cuenta_gana_el_nombre():
    assert _pcn("CIVE20", "VEHICULO", "FURGONETA 1234ABC") == (
        _e(60503), "auto_nombre")


def test_f068_r5_varias_con_su_cuenta_gana_por_categoria():
    cuentas = {**CUENTAS, 60502: "0678.CIVE20"}
    assert _pcn("CIVE20", "GASOIL", None, cuentas) == (
        _e(60504), "auto_categoria")


@pytest.mark.parametrize("tipo_res, descripcion", [
    (None, None), ("TELEFONIA", "MOVIL 600"), ("XXXX", "YYYY ZZZZ")])
def test_f068_r7_varias_con_su_cuenta_empatadas_gana_el_ci4(tipo_res,
                                                           descripcion):
    """D5-A: con varias de su cuenta, «ninguna casa» es un empate a 0 y
    decide el CI.4; con las dos iguales por nombre, también."""
    assert _pcn("CICO13", tipo_res, descripcion) == (
        _e(60401), METODO_CAPITULO_CI4)
    assert _pcn("CICO01", tipo_res, descripcion) == (
        _e(60402), METODO_CAPITULO_CI4)
    assert _pcn("CICO15", tipo_res, descripcion) == (
        _e(60403), METODO_CAPITULO_CI4)


def test_f068_r7_el_ci4_solo_desempata_entre_las_del_maximo():
    """La del CI.4 a 0 no gana a la que casa: el máximo único manda."""
    cuentas = {**CUENTAS, 60502: "0678.CICO13"}
    assert _pcn("CICO13", "TELEFONO", "TELEFONO MOVIL 600", cuentas) == (
        _e(60502), "auto_nombre")


def test_f068_r7_empate_entre_las_del_maximo_sin_la_de_abajo():
    """Empatan a 0,9 dos `LIMPIEZA` que no son del CI.4; la del CI.4 a 0
    (`COMBUSTIBLE`) no entra en el desempate: sin partida."""
    cuentas = {60105: "0678.CIXX01", 60302: "0678.CIXX01",
               60402: "0678.CIXX01"}
    assert _pcn("CIXX01", "LIMPIEZA", None, cuentas) == (
        None, MOTIVO_VARIAS_CI)


@pytest.mark.parametrize("sub", ["CIMP09", "CIME20"])
def test_f068_r9_varias_con_su_cuenta_sin_desempate_sin_partida(sub):
    """`CIMP09`: `CI.0.06` / `CI.03P.9`, ninguna del CI.4; `CIME20`:
    `CI.4.20` / `CI.04.21`, las dos."""
    assert _pcn(sub) == (None, MOTIVO_VARIAS_CI)
    assert _pcn(sub, "VEHICULOS", None) == (None, MOTIVO_VARIAS_CI)


@pytest.mark.parametrize("sub", [None, "", "CIZZ99"])
def test_f068_r6_sin_su_cuenta_casa_por_nombre_entre_las_ci(sub):
    assert _pcn(sub, "TELEFONO", "TELEFONO MOVIL 600") == (
        _e(60502), "auto_nombre")


def test_f068_r6_sin_su_cuenta_empate_lo_decide_el_ci4():
    assert _pcn(None, "TELEFONIA", "MOVIL 600") == (
        _e(60401), METODO_CAPITULO_CI4)


@pytest.mark.parametrize("tipo_res", ["LIMPIEZA", "MENSAJERIA"])
def test_f068_r9_sin_su_cuenta_empate_sin_desempate(tipo_res):
    """`LIMPIEZA`: `CI.0.20` / `CI.03P.20`, ninguna del CI.4;
    `MENSAJERIA`: `CI.4.20` / `CI.04.21`, las dos."""
    assert _pcn(None, tipo_res, None) == (None, MOTIVO_EMPATE_NOMBRE)


@pytest.mark.parametrize("tipo_res, descripcion", [
    (None, None), ("XXXX", "YYYY ZZZZ"),
    # Solo casaría una hoja que no es CI* o un capítulo: no cuentan.
    ("HORMIGON", None), ("SEGUROS DECENALES", None), ("PERSONAL", None),
    ("CAPITULO", None)])
def test_f068_r6_sin_su_cuenta_y_nada_casa_sin_partida(tipo_res,
                                                       descripcion):
    """Solo las que casan: sin ninguna, sin partida, aunque haya hojas del
    CI.4 (el CI.4 a 0 solo decide entre las de su cuenta, D5)."""
    assert _pcn("CIZZ99", tipo_res, descripcion) == (None, MOTIVO_SIN_CI)


def test_f068_r6_sin_su_cuenta_no_cuenta_la_de_baja():
    """Las dos `TELEFONIA` activas empatan; la de baja (`CI.4.99`) no entra:
    si entrara, habría dos del CI.4 y no desempataría."""
    assert _pcn(None, "TELEFONIA", None) == (_e(60401), METODO_CAPITULO_CI4)


def test_f068_r9_textos_de_los_motivos():
    assert por_que_sin_ci(MOTIVO_SIN_CI) == (
        "ninguna partida del presupuesto tiene la cuenta de su tipo y ni el "
        "historial ni el nombre deciden")
    assert por_que_sin_ci(MOTIVO_VARIAS_CI) == (
        "varias partidas del presupuesto tienen la cuenta de su tipo y ni el "
        "historial, ni el nombre ni el capítulo CI.4 deciden")
    assert por_que_sin_ci(MOTIVO_EMPATE_NOMBRE) == (
        "ninguna partida del presupuesto tiene la cuenta de su tipo y varias "
        "casan por nombre: ni el historial ni el capítulo CI.4 deciden")


@pytest.mark.parametrize("motivo", [MOTIVO_SIN_CI, MOTIVO_VARIAS_CI,
                                    MOTIVO_EMPATE_NOMBRE])
def test_f068_r9_el_aviso_cabe_en_sigrid_motivo(motivo):
    aviso = AVISO_SIN_PARTIDA_VINCULADO.format(
        tipo="X" * 10, cod="Y" * 20, por_que=por_que_sin_ci(motivo))
    assert len(aviso) <= 300


# ============================ R1-R3, R10 (T4) ============================ #
OBRA = 678000
OTRA = 692000


def _l(mes: int, paride: int, can: float = 1.0, *, recurso: int = 10,
       obra: int = OBRA, ano: int = 2026, parte: str = "PT26/00300",
       obra_cod: str = "0678") -> LineaHistorial:
    """Una línea del historial con la forma de `historial_de_vinculados`
    (la de `LineaHistorial`): el código y la descripción de su partida,
    los del presupuesto."""
    n = _hojas().get(paride)
    return LineaHistorial(
        reside=recurso, obride=obra, obra_cod=obra_cod, parte_cod=parte,
        ano=ano, mes=mes, can=can, paride=paride,
        par_cod=n.cod if n else "CI.9.9", par_res=n.res if n else "OTRA")


def _ph(historial, recurso=10, obra=OBRA):
    return partida_por_historial(historial, recurso, obra, _hojas())


def test_f068_r2_la_del_ultimo_mes_en_la_obra_con_su_origen():
    """El caso de la 0678: el teléfono, siempre en `CI.4.13`."""
    assert _ph([_l(8, 60401), _l(9, 60401, parte="PT26/00321"),
                _l(7, 60101)]) == PartidaElegida(
        paride=60401, cod="CI.4.13", res="TELEFONIA",
        origen="parte PT26/00321 · 09/2026 · obra 0678")


def test_f068_r2_ultimo_mes_aunque_antes_fuera_a_otra():
    assert _ph([_l(3, 60401), _l(3, 60401), _l(4, 60101, 0.1)]).paride == (
        60101)


def test_f068_r2_ultimo_mes_cruza_el_ano():
    assert _ph([_l(12, 60401, ano=2025), _l(1, 60101, ano=2026)]).paride == (
        60101)


def test_f068_r2_gana_la_de_mas_can_sumado():
    assert _ph([_l(9, 60101, 0.5), _l(9, 60401, 0.3),
                _l(9, 60401, 0.3)]).paride == 60401
    assert _ph([_l(9, 60101, 0.7), _l(9, 60401, 0.3),
                _l(9, 60401, 0.3)]).paride == 60101


def test_f068_r2_empate_no_propone():
    assert _ph([_l(9, 60101, 0.5), _l(9, 60401, 0.5)]) is None


def test_f068_r2_la_ganadora_que_no_es_hoja_activa_no_propone():
    """De baja (`CI.4.99`), un capítulo (`CI.4`) o fuera del presupuesto."""
    for paride in (60404, 60400, 99999):
        assert _ph([_l(9, paride), _l(8, 60401)]) is None


def test_f068_r2_d2_solo_las_lineas_en_partidas_ci():
    """D2-A: el mes en que fue a una `CP*` o una `CD*` no cuenta; se toma el
    último mes de las `CI*`."""
    assert _ph([_l(9, 60801), _l(9, 60901), _l(8, 60401)]).paride == 60401
    assert _ph([_l(9, 60801), _l(9, 60401, 0.1)]).paride == 60401
    assert _ph([_l(9, 60801)]) is None


def test_f068_r2_d2_la_prueba_ci_es_por_codigo_de_la_linea():
    linea = _l(9, 60401)
    otra = LineaHistorial(**{**linea.__dict__, "par_cod": " ci.4.13 "})
    sin = LineaHistorial(**{**linea.__dict__, "par_cod": None})
    assert _ph([otra]).paride == 60401
    assert _ph([sin]) is None


def test_f068_r2_solo_ese_recurso_y_esa_obra():
    assert _ph([_l(9, 60101, recurso=11), _l(9, 60101, obra=OTRA),
                _l(5, 60401)]).paride == 60401
    assert _ph([_l(9, 60101, recurso=11), _l(9, 60101, obra=OTRA)]) is None
    assert _ph([]) is None


def test_f068_r2_la_linea_sin_partida_no_cuenta():
    assert _ph([_l(9, 0), _l(8, 60401)]).paride == 60401


def test_f068_r3_la_misma_funcion_que_el_trabajador(monkeypatch):
    """R3: el paso es `previa_en_obra` del trabajador, no una copia: se
    llama con las líneas `CI*`, el recurso, la obra y las hojas activas."""
    assert rv.previa_en_obra is propuesta_partida.previa_en_obra
    llamadas = []

    def espia(historial, recurso, obra_ide, hojas):
        llamadas.append((list(historial), recurso, obra_ide, sorted(hojas)))
        return propuesta_partida.previa_en_obra(historial, recurso,
                                                obra_ide, hojas)

    monkeypatch.setattr(rv, "previa_en_obra", espia)
    ci, cp = _l(9, 60401), _l(9, 60801)
    assert _ph([ci, cp]).paride == 60401
    [(lineas, recurso, obra, hojas)] = llamadas
    assert (lineas, recurso, obra) == ([ci], 10, OBRA)
    activas = {i for i, n in _hojas().items() if n.es_hoja and n.activa}
    assert set(hojas) == activas and 60404 not in hojas


# ---- el orden (R1) ---- #
def _titular(destino: str = "obra", paride: int = 60501,
             cod: str | None = "CI.5.1", res: str | None = "JEFE DE OBRA",
             metodo: str | None = "parte_anterior") -> PartidaTitular:
    return PartidaTitular(destino=destino, paride=paride, cod=cod, res=res,
                          metodo=metodo)


class _Paso:
    """Un paso de la regla como función: apunta si se ha pedido."""

    def __init__(self, resultado) -> None:
        self.llamadas = 0
        self.resultado = resultado

    def __call__(self):
        self.llamadas += 1
        return self.resultado


PREVIA = PartidaElegida(paride=60401, cod="CI.4.13", res="TELEFONIA",
                        origen="parte PT26/00321 · 09/2026 · obra 0678")


def test_f068_r1_el_historial_va_antes_que_la_cuenta():
    hist, ci = _Paso(PREVIA), _Paso((_e(60101), METODO_CI_TIPO))
    r = partida_del_vinculado(_titular(), None, True, ci, hist)
    assert r == PartidaVinculado(
        paride=60401, cod="CI.4.13", res="TELEFONIA",
        metodo=METODO_PARTE_ANTERIOR,
        origen="parte PT26/00321 · 09/2026 · obra 0678")
    assert (hist.llamadas, ci.llamadas) == (1, 0)


@pytest.mark.parametrize("ide, metodo", [
    (60501, METODO_CI_TIPO), (60502, "auto_nombre"),
    (60401, METODO_CAPITULO_CI4)])
def test_f068_r1_sin_historial_la_cuenta_y_el_nombre(ide, metodo):
    """El método es el que da el paso (ya no siempre `ci_tipo`)."""
    hist, ci = _Paso(None), _Paso((_e(ide), metodo))
    r = partida_del_vinculado(_titular(), None, True, ci, hist)
    n = _hojas()[ide]
    assert r == PartidaVinculado(paride=ide, cod=n.cod, res=n.res,
                                 metodo=metodo)
    assert (hist.llamadas, ci.llamadas) == (1, 1)


@pytest.mark.parametrize("motivo", [MOTIVO_SIN_CI, MOTIVO_VARIAS_CI,
                                    MOTIVO_EMPATE_NOMBRE])
def test_f068_r9_ningun_paso_sin_partida_con_su_motivo(motivo):
    r = partida_del_vinculado(_titular(), None, True, _Paso((None, motivo)),
                              _Paso(None))
    assert r == PartidaVinculado(motivo=motivo, sin_partida=True)
    assert not r.omitir and r.paride == 0


def test_f068_r1_elegida_y_titular_antes_que_el_historial():
    hist, ci = _Paso(PREVIA), _Paso((_e(60101), METODO_CI_TIPO))
    elegida = PartidaElegida(paride=60402, cod="CI.4.1", res="COMBUSTIBLE")
    assert partida_del_vinculado(_titular(), elegida, True, ci,
                                 hist).metodo == METODO_MANUAL
    assert partida_del_vinculado(_titular(), elegida, False, ci,
                                 hist).motivo == (
        MOTIVO_ELEGIDA_NO_VALIDA.format(cod="CI.4.1"))
    t = _titular(paride=60801, cod="CP.1", res="SEGUROS DECENALES")
    assert partida_del_vinculado(t, None, True, ci, hist).metodo == (
        METODO_TITULAR)
    assert (hist.llamadas, ci.llamadas) == (0, 0)


def test_f068_r1_sin_paso_de_historial_el_orden_de_f044():
    """`historial=None`: las llamadas de F-044 siguen valiendo."""
    ci = _Paso((_e(60501), METODO_CI_TIPO))
    r = partida_del_vinculado(_titular(), None, True, ci)
    assert (r.paride, r.metodo, r.origen) == (60501, METODO_CI_TIPO, None)


def test_f068_r1_titular_sin_partida_tambien_mira_el_historial():
    hist = _Paso(PREVIA)
    t = _titular(paride=0, cod=None, res=None, metodo=None)
    assert partida_del_vinculado(t, None, True, _Paso((None, MOTIVO_SIN_CI)),
                                 hist).paride == 60401


def test_f068_r1_el_origen_de_la_cuenta_pasa_tal_cual():
    con_origen = PartidaElegida(paride=60501, cod="CI.5.1", res="JEFE",
                                origen="algo")
    r = partida_del_vinculado(_titular(), None, True,
                              _Paso((con_origen, METODO_CI_TIPO)),
                              _Paso(None))
    assert r.origen == "algo"


def test_f068_r10_las_reglas_no_leen_nada():
    """Sin I/O: el módulo no importa clientes, httpx ni infraestructura; el
    historial y las cuentas llegan como funciones."""
    arbol = ast.parse(Path(rv.__file__).read_text(encoding="utf-8"))
    importados = {n.module or "" for n in ast.walk(arbol)
                  if isinstance(n, ast.ImportFrom)}
    importados |= {a.name for n in ast.walk(arbol)
                   if isinstance(n, ast.Import) for a in n.names}
    assert not any(i.startswith(("infrastructure", "httpx", "requests"))
                   for i in importados), importados


@pytest.mark.parametrize("historial, sub, tipo_res", [
    ([_l(9, 60404)], "CICO13", None),
    ([], None, "CAPITULO"),
    ([], None, "PERSONAL"),
    ([_l(9, 60400)], "CIZZ99", None),
])
def test_f068_r10_toda_propuesta_es_hoja_activa(historial, sub, tipo_res):
    """Lo que no es hoja activa (de baja, capítulo) nunca sale: ni por el
    historial ni por el nombre."""
    hojas = _hojas()
    r = partida_del_vinculado(
        _titular(), None, True,
        lambda: partida_por_cuenta_o_nombre(hojas, CUENTAS, sub, tipo_res,
                                            None),
        lambda: partida_por_historial(historial, 10, OBRA, hojas))
    assert r.paride == 0 or (hojas[r.paride].es_hoja
                             and hojas[r.paride].activa)
    assert r.paride not in (60404, 60400, 60500)
