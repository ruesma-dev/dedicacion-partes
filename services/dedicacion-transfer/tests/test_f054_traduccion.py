# tests/test_f054_traduccion.py
"""F-054 · T2: `porcentajes_existentes.py` (R5, R8-R12; design §4.2).

Lo que se comprueba:

- R5: las líneas de la obra de pruebas solo se cuentan
  (`excluidas_pruebas`), nunca se traducen ni salen en `lineas`.
- R8: una línea de una obra normal sale con `destino = normal`.
- R9: una de la obra de postventa sale con `destino = postventa` y la ÚNICA
  obra, de las que manda la api, cuyo `casar_postventa` da su partida;
  ninguna o varias ⇒ motivo. Sin catálogo (registro de postventa apagado),
  el motivo del catálogo.
- R10: una de la obra VAR, `var_paride` si `partida_var_de` la acepta; si
  no, motivo (fuera del universo; sin obra VAR, normal).
- R11: los catálogos de postventa y VAR se leen solo si alguna línea es de
  esa obra (lecturas contadas).
- R12: traducir y luego casar con las funciones del preflight da la misma
  partida.
- Filas barajadas, mismo resultado.

Sin red ni BBDD: `ClienteVar` de `test_f039_universo_var.py` con las
líneas mensuales en memoria. Los `ide` son inventados.
"""
from __future__ import annotations

import random

import pytest
from application.services.porcentajes_existentes import (
    MOTIVO_PV_NINGUNA,
    MOTIVO_PV_VARIAS,
    PorcentajesExistentes,
    obras_por_partida,
    traducir,
)
from application.services.reglas_porcentajes import MOTIVO_POSTVENTA_OFF
from application.services.universo_postventa import (
    cargar_catalogo_postventa,
    casar_postventa,
)
from application.services.universo_var import (
    MOTIVO_VAR_FUERA,
    cargar_catalogo_var,
    partida_var_de,
)
from domain.models.registro_models import LineaMensualSigrid, ObraEntrada

from tests.conftest import OBRA_ORIGEN, OBRA_POSTVENTA, OBRA_PRUEBAS
from tests.test_f039_universo_var import (
    DESDE,
    OBRA_VAR,
    VAR_IDE,
    ClienteVar,
    ajustes_var,
)

PV_IDE = 999001
P29 = 417055
#: Obras que manda la api (las de `admite_postventa`).
O0678 = ObraEntrada(ide=555001, codigo=OBRA_ORIGEN, nombre="15 VIVIENDAS")
O0713 = ObraEntrada(ide=555713, codigo="0713", nombre="CLUB DEPORTIVO")
#: Otra obra con el mismo código que la 0678 (otra ficha): casa la misma.
O0678_BIS = ObraEntrada(ide=555999, codigo=OBRA_ORIGEN, nombre="OTRA")


def _l(ide: int, obra_ide: int, obra_cod: str, *, paride: int = 0,
       recurso: int = 200, can: float = 0.5) -> LineaMensualSigrid:
    return LineaMensualSigrid(
        hmores_ide=ide, recurso_ide=recurso, obra_ide=obra_ide,
        obra_cod=obra_cod, parte_ide=7000 + obra_ide % 1000,
        parte_cod="PT26/00001", parte_est=1, en_registro=True, hora="MENC",
        can=can, fec=20260930, paride=paride, partida_cod=None,
        partida_res=None, synckey=None)


class ClienteExistentes(ClienteVar):
    """`ClienteVar` con las líneas mensuales del periodo y cada llamada a
    su lectura anotada (sus argumentos)."""

    def __init__(self, mensuales=(), **kw) -> None:
        super().__init__(**kw)
        self.mensuales = list(mensuales)
        self.leidas_mensuales: list[tuple] = []

    def lineas_mensuales_del_periodo(self, empresa, ano, mes, resides=None,
                                     solo_m=True):
        self.leidas_mensuales.append((empresa, ano, mes, resides, solo_m))
        return list(self.mensuales)


def _calcular(lineas, obras=(O0678, O0713), cli=None, **ajustes):
    cli = cli or ClienteExistentes(lineas)
    r = PorcentajesExistentes(cliente=cli, settings=ajustes_var(
        **ajustes)).calcular(1, 2026, 9, list(obras))
    return r, cli


# ============================ R5 · pruebas ============================== #
def test_f054_r5_las_de_la_obra_de_pruebas_solo_se_cuentan():
    r, cli = _calcular([_l(1, 828942, OBRA_PRUEBAS), _l(2, 694, "0694"),
                        _l(3, 828942, OBRA_PRUEBAS)])
    assert r["lineas_leidas"] == 3
    assert r["excluidas_pruebas"] == 2
    assert [x["hmores_ide"] for x in r["lineas"]] == [2]
    assert cli.leidas_mensuales == [(1, 2026, 9, None, True)]


def test_f054_r5_traducir_una_de_pruebas_es_none():
    assert traducir(_l(1, 828942, OBRA_PRUEBAS), cod_pruebas=OBRA_PRUEBAS,
                    cod_postventa=OBRA_POSTVENTA, cod_var=OBRA_VAR,
                    inverso={}, catalogo_var=None, desde=DESDE) is None


# ============================ R8 · normal =============================== #
def test_f054_r8_obra_normal_destino_normal_con_lo_de_r6():
    r, _ = _calcular([_l(2, 694, "0694", paride=2105, can=0.95)])
    [x] = r["lineas"]
    assert x == {
        "hmores_ide": 2, "recurso_ide": 200, "obra_ide": 694,
        "obra_cod": "0694", "parte_ide": 7694, "parte_cod": "PT26/00001",
        "parte_est": 1, "en_registro": True, "hora": "MENC", "can": 0.95,
        "fec": 20260930, "paride": 2105, "partida_cod": None,
        "partida_res": None, "synckey": None, "destino": "normal",
        "obra_origen_ide": None, "var_paride": None, "motivo": None}
    assert r["obra_postventa"] is None and r["motivo_postventa"] is None
    assert r["obra_var"] is None and r["motivo_var"] is None


# =========================== R9 · postventa ============================= #
def test_f054_r9_postventa_con_una_obra_que_casa():
    r, _ = _calcular([_l(3, PV_IDE, OBRA_POSTVENTA, paride=70001)])
    [x] = r["lineas"]
    assert (x["destino"], x["obra_origen_ide"], x["motivo"]) == (
        "postventa", 555001, None)
    assert r["obra_postventa"]["ide"] == PV_IDE
    assert r["motivo_postventa"] is None


def test_f054_r9_postventa_sin_obra_que_case_es_motivo():
    r, _ = _calcular([_l(3, PV_IDE, OBRA_POSTVENTA, paride=70002)],
                     obras=[O0678])
    [x] = r["lineas"]
    assert x["destino"] == "postventa" and x["obra_origen_ide"] is None
    assert x["motivo"] == MOTIVO_PV_NINGUNA.format(
        partida=70002, pv=OBRA_POSTVENTA)


def test_f054_r9_postventa_con_dos_obras_que_casan_es_motivo():
    r, _ = _calcular([_l(3, PV_IDE, OBRA_POSTVENTA, paride=70001)],
                     obras=[O0678_BIS, O0713, O0678])
    [x] = r["lineas"]
    assert x["obra_origen_ide"] is None
    assert x["motivo"] == MOTIVO_PV_VARIAS.format(
        partida=70001, pv=OBRA_POSTVENTA, obras="555001, 555999")


def test_f054_r9_postventa_sin_partida_es_motivo():
    r, _ = _calcular([_l(3, PV_IDE, OBRA_POSTVENTA, paride=0)])
    assert r["lineas"][0]["motivo"] == MOTIVO_PV_NINGUNA.format(
        partida=0, pv=OBRA_POSTVENTA)


def test_f054_r9_postventa_apagada_el_motivo_del_catalogo():
    r, cli = _calcular([_l(3, PV_IDE, OBRA_POSTVENTA, paride=70001)],
                       postventa_registrar=False)
    [x] = r["lineas"]
    assert x["destino"] == "postventa" and x["obra_origen_ide"] is None
    assert x["motivo"] == MOTIVO_POSTVENTA_OFF
    assert r["motivo_postventa"] == MOTIVO_POSTVENTA_OFF
    assert r["obra_postventa"] is None
    assert cli.n_capitulos_de_obra == 0


def test_f054_r9_obras_por_partida_es_el_casado_inverso():
    cli = ClienteVar()
    catalogo = cargar_catalogo_postventa(cli, ajustes_var(), 1)
    inverso = obras_por_partida(catalogo, [O0678_BIS, O0713, O0678])
    assert {k: [o.ide for o in v] for k, v in inverso.items()} == {
        70001: [555001, 555999], 70002: [555713]}


# ============================== R10 · VAR =============================== #
def test_f054_r10_var_dentro_del_universo():
    r, _ = _calcular([_l(4, VAR_IDE, OBRA_VAR, paride=P29)])
    [x] = r["lineas"]
    assert (x["destino"], x["var_paride"], x["motivo"]) == ("var", P29, None)
    assert r["obra_var"]["ide"] == VAR_IDE and r["motivo_var"] is None


def test_f054_r10_var_fuera_del_universo_es_motivo():
    r, _ = _calcular([_l(4, VAR_IDE, OBRA_VAR, paride=417002)])
    [x] = r["lineas"]
    assert (x["destino"], x["var_paride"]) == ("var", None)
    assert x["motivo"] == MOTIVO_VAR_FUERA.format(paride=417002,
                                                  var=OBRA_VAR, desde=DESDE)


def test_f054_r10_sin_obra_var_la_linea_es_normal():
    r, cli = _calcular([_l(4, VAR_IDE, OBRA_VAR, paride=P29)],
                       var_obra_cod="")
    [x] = r["lineas"]
    assert (x["destino"], x["var_paride"], x["motivo"]) == (
        "normal", None, None)
    assert r["obra_var"] is None and r["motivo_var"] is None
    assert cli.n_obra_por_codigo == 0


# ======================= R11 · catálogos solo si hacen falta ============ #
def test_f054_r11_sin_lineas_de_esas_obras_no_se_lee_ningun_catalogo():
    _, cli = _calcular([_l(2, 694, "0694"), _l(1, 828942, OBRA_PRUEBAS)])
    assert cli.n_obra_por_codigo == 0 and cli.n_capitulos_de_obra == 0


def test_f054_r11_solo_postventa_lee_solo_su_catalogo():
    _, cli = _calcular([_l(3, PV_IDE, OBRA_POSTVENTA, paride=70001)] * 2)
    assert (cli.n_obra_por_codigo, cli.n_capitulos_de_obra) == (1, 1)


def test_f054_r11_solo_var_lee_solo_su_catalogo():
    _, cli = _calcular([_l(4, VAR_IDE, OBRA_VAR, paride=P29)] * 2)
    assert (cli.n_obra_por_codigo, cli.n_capitulos_de_obra) == (1, 1)


def test_f054_r11_las_dos_una_vez_cada_una():
    _, cli = _calcular([_l(3, PV_IDE, OBRA_POSTVENTA, paride=70001),
                        _l(4, VAR_IDE, OBRA_VAR, paride=P29),
                        _l(5, PV_IDE, OBRA_POSTVENTA, paride=70002)])
    assert (cli.n_obra_por_codigo, cli.n_capitulos_de_obra) == (2, 2)


# ============ R12 · traducir y casar dan la misma partida =============== #
@pytest.mark.parametrize("paride", [70001, 70002])
def test_f054_r12_traducir_y_casar_misma_partida(paride):
    cli = ClienteVar()
    st = ajustes_var()
    r, _ = _calcular([_l(3, PV_IDE, OBRA_POSTVENTA, paride=paride)])
    origen = {o.ide: o for o in (O0678, O0713)}[
        r["lineas"][0]["obra_origen_ide"]]
    partida, motivo = casar_postventa(
        cargar_catalogo_postventa(cli, st, 1), origen.codigo, origen.nombre)
    assert motivo is None and partida["ide"] == paride


def test_f054_r12_var_aceptada_es_la_del_preflight():
    cli = ClienteVar()
    r, _ = _calcular([_l(4, VAR_IDE, OBRA_VAR, paride=P29)])
    nodo, motivo = partida_var_de(
        cargar_catalogo_var(cli, ajustes_var(), 1), VAR_IDE,
        r["lineas"][0]["var_paride"], DESDE)
    assert motivo is None and nodo.ide == P29


# ======================= Orden: filas barajadas ========================= #
def test_f054_filas_barajadas_mismo_resultado():
    lineas = [_l(9, 694, "0694"), _l(3, PV_IDE, OBRA_POSTVENTA, paride=70001),
              _l(1, 828942, OBRA_PRUEBAS), _l(7, VAR_IDE, OBRA_VAR,
                                              paride=P29),
              _l(5, PV_IDE, OBRA_POSTVENTA, paride=70002)]
    base, _ = _calcular(lineas)
    assert [x["hmores_ide"] for x in base["lineas"]] == [3, 5, 7, 9]
    for semilla in range(5):
        barajadas = list(lineas)
        random.Random(semilla).shuffle(barajadas)
        obras = [O0713, O0678]
        random.Random(semilla).shuffle(obras)
        assert _calcular(barajadas, obras=obras)[0] == base


def test_f054_r3_un_fallo_de_lectura_sube():
    class Falla(ClienteExistentes):
        def lineas_mensuales_del_periodo(self, *a, **k):
            raise RuntimeError("sigrid-api read HTTP 502")

    with pytest.raises(RuntimeError, match="502"):
        _calcular([], cli=Falla())
