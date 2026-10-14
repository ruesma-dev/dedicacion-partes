# tests/test_f050_propuesta.py
"""F-050 · Propuesta de partida del transfer (R1-R7, R10).

`application/services/propuesta_partida.py` es puro: se prueba en memoria
con presupuestos (`obrparpar`) y líneas de historial (`hmores`) inventados.
La lectura del historial (`historial_partidas`, T2) se prueba con el `_read`
del cliente sustituido por uno falso que anota el SQL y los parámetros.

Los dos casos reales de `design.md` §5.1 (leídos en Sigrid el 2026-10-09,
solo lectura): `01.19.03.20` «…PROPORCI…» de la 0694 y `1.4.1.8` «…COSTES
INDIRECTOS…» de la 0404, ambas bajo la raíz `CD`. Los `ide` son inventados.
Sin red ni BBDD.
"""
from __future__ import annotations

import random

import pytest
from application.services.partida_resolver import construir_catalogo
from application.services.propuesta_partida import (
    LineaHistorial,
    Propuesta,
    catalogo,
    clave_orden_codigo,
    mayor_de,
    mayor_inicial,
    previa_en_obra,
    proponer_partida,
    ultima_de_recurso,
    ventana,
)

from tests.conftest import _fila

OBRA = 694          # obra de la línea (origen)
OTRA = 696          # otra obra del mismo recurso
RECURSO = 4321

#: Presupuesto de la obra de la línea: tres raíces como en Sigrid (`CD`,
#: `CI`, `CP`), una hoja dada de baja y dos hojas con el mismo código y
#: descripción en capítulos distintos (traslado ambiguo).
PRESUPUESTO = [
    _fila(1000, 0, 0, "CD", "COSTES DIRECTOS"),
    _fila(1001, 1000, 1, "01.19.03.20", "PARTIDA PROPORCIONAL DE MEDIOS"),
    _fila(1002, 1000, 2, "1.4.1.8", "COSTES INDIRECTOS DE ESTRUCTURA"),
    _fila(2000, 0, 3, "CI", "COSTES INDIRECTOS"),
    _fila(2100, 2000, 4, "CI.1", "PERSONAL"),
    _fila(2105, 2100, 5, "CI.1.5", "JEFE DE OBRA"),
    _fila(2108, 2100, 6, "CI.1.8", "ENCARGADO (ACUNA)"),
    _fila(2109, 2100, 7, "CI.1.9", "ADMINISTRATIVO"),
    _fila(2110, 2100, 8, "CI.1.10", "TOPOGRAFO"),
    _fila(2111, 2100, 9, "CI.1.11", "VIGILANTE", tipdes=1),
    _fila(2200, 2000, 10, "CI.2", "VARIOS"),
    _fila(2201, 2200, 11, "CI.2.1", "OFICIAL (REMATES)"),
    _fila(2300, 2000, 12, "CI.3", "VARIOS BIS"),
    _fila(2301, 2300, 13, "CI.3.1", "OFICIAL (REMATES)"),
    _fila(3000, 0, 14, "CP", "COSTES PROPORCIONALES"),
    _fila(3001, 3000, 15, "CP.1", "SEGUROS"),
    _fila(3002, 3000, 16, "CP.12", "SEGURIDAD Y SALUD"),
]


def _nodos(filas=None):
    return construir_catalogo(list(filas or PRESUPUESTO))


def _h(*, obra=OBRA, ano=2026, mes=9, can=1.0, paride=2105, cod="CI.1.5",
       res="JEFE DE OBRA", parte="PT26/00319", obra_cod=None,
       recurso=RECURSO) -> LineaHistorial:
    return LineaHistorial(
        reside=recurso, obride=obra,
        obra_cod=obra_cod or f"0{obra}", parte_cod=parte, ano=ano, mes=mes,
        can=can, paride=paride, par_cod=cod, par_res=res)


def _hojas(nodos):
    return {n.ide: n for n in nodos.values() if n.es_hoja and n.activa}


# ============================== R10 · orden ============================== #
def test_f050_r10_orden_natural_ci_1_9_antes_que_ci_1_10():
    codigos = ["CI.1.10", "CI.1.9", "CI.1", "CI.2.1", "CD", "01.19.03.20",
               "1.4.1.8", "ci.1.8", None, "CP.12", "CP.1"]
    ordenados = sorted(codigos, key=clave_orden_codigo)
    assert ordenados == [None, "1.4.1.8", "01.19.03.20", "CD", "CI.1",
                         "ci.1.8", "CI.1.9", "CI.1.10", "CI.2.1", "CP.1",
                         "CP.12"]


def test_f050_r10_orden_natural_ignora_mayusculas_y_espacios_de_borde():
    assert clave_orden_codigo(" ci.1.9 ") == clave_orden_codigo("CI.1.9")
    assert clave_orden_codigo("CI.01") == clave_orden_codigo("CI.1")
    assert clave_orden_codigo("") == clave_orden_codigo(None) == ()
    # Un dígito que no es ASCII («²») no es un número: no rompe el orden.
    assert sorted(["12", "1²", "10"], key=clave_orden_codigo) == [
        "1²", "10", "12"]


def test_f050_r10_catalogo_hojas_activas_en_orden_natural_con_mayor():
    cat = catalogo(_nodos(list(reversed(PRESUPUESTO))))
    assert [p["cod"] for p in cat] == [
        "1.4.1.8", "01.19.03.20", "CI.1.5", "CI.1.8", "CI.1.9", "CI.1.10",
        "CI.2.1", "CI.3.1", "CP.1", "CP.12"]
    assert cat[1] == {"ide": 1001, "cod": "01.19.03.20",
                      "res": "PARTIDA PROPORCIONAL DE MEDIOS",
                      "categoria": "CP", "mayor": "CD"}
    assert {p["mayor"] for p in cat[2:8]} == {"CI"}
    assert [p["mayor"] for p in cat[8:]] == ["CP", "CP"]


def test_f050_r10_catalogo_desempata_por_ide_y_vacio_sin_nodos():
    filas = [_fila(9, 0, 0, "CI", "COSTES INDIRECTOS"),
             _fila(12, 9, 1, "CI.1", "B"), _fila(11, 9, 2, "CI.1", "A")]
    assert [p["ide"] for p in catalogo(_nodos(filas))] == [11, 12]
    assert catalogo({}) == []


# ============================ mayor por la raíz =========================== #
def test_f050_mayor_casos_reales_bajo_cd_salen_cd():
    """`categoria` de la copia de `partes` las clasifica mal (CP y CI); el
    mayor sube a la raíz `CD`."""
    nodos = _nodos()
    assert nodos[1001].categoria == "CP" and nodos[1002].categoria == "CI"
    assert mayor_de(nodos, nodos[1001]) == "CD"
    assert mayor_de(nodos, nodos[1002]) == "CD"
    assert mayor_de(nodos, nodos[2105]) == "CI"
    assert mayor_de(nodos, nodos[3002]) == "CP"


def test_f050_mayor_raiz_ci0_y_raiz_por_descripcion():
    filas = [_fila(1, 0, 0, "CI0", "OTRA COSA"),
             _fila(2, 1, 1, "X.1", "ENCARGADO"),
             _fila(3, 0, 2, "Z", "COSTES PROPORCIONALES"),
             _fila(4, 3, 3, "Z.1", "SEGUROS")]
    nodos = _nodos(filas)
    assert mayor_de(nodos, nodos[2]) == "CI"
    assert mayor_de(nodos, nodos[4]) == "CP"


def test_f050_mayor_raiz_sin_mayor_usa_la_categoria_de_la_hoja():
    filas = [_fila(1, 0, 0, "PRES", "PRESUPUESTO"),
             _fila(2, 1, 1, "CI", "COSTES INDIRECTOS"),
             _fila(3, 2, 2, "CI.1", "ENCARGADO"),
             _fila(4, 1, 3, "9", "VARIOS")]
    nodos = _nodos(filas)
    assert mayor_de(nodos, nodos[3]) == "CI"
    assert mayor_de(nodos, nodos[4]) == "OTRO"


def test_f050_mayor_corta_los_ciclos():
    filas = [_fila(1, 2, 0, "A", "COSTES DIRECTOS"),
             _fila(2, 1, 1, "B", "COSTES PROPORCIONALES"),
             _fila(3, 3, 2, "C", "COSTES INDIRECTOS")]
    nodos = _nodos(filas)
    assert mayor_de(nodos, nodos[1]) == "CP"
    assert mayor_de(nodos, nodos[2]) == "CD"
    assert mayor_de(nodos, nodos[3]) == "CI"


def test_f050_mayor_padre_fuera_del_presupuesto_es_raiz():
    nodos = _nodos([_fila(5, 777, 0, "CP.3", "AVALES")])
    assert mayor_de(nodos, nodos[5]) == "CP"


# ============================== ventana ================================== #
@pytest.mark.parametrize("ano, mes, atras, esperado", [
    (2026, 9, 24, (202409, 202609)),
    (2026, 1, 1, (202512, 202601)),
    (2026, 12, 12, (202512, 202612)),
    (2026, 3, 0, (202603, 202603)),
    (2026, 2, 26, (202312, 202602)),
])
def test_f050_r1_ventana_periodo_incluido_y_meses_atras(ano, mes, atras,
                                                         esperado):
    assert ventana(ano, mes, atras) == esperado


# ============================ R1 · paso 1 ================================ #
def test_f050_r1_paso1_parte_anterior_de_esa_obra_mes_mas_reciente():
    hist = [_h(mes=7, paride=2108, cod="CI.1.8", res="ENCARGADO (ACUNA)"),
            _h(mes=9, can=0.4, parte="PT26/00319"),
            _h(obra=OTRA, mes=10, paride=2109, cod="CI.1.9",
               res="ADMINISTRATIVO")]
    p = previa_en_obra(hist, RECURSO, OBRA, _hojas(_nodos()))
    assert p == Propuesta(paride=2105, cod="CI.1.5", res="JEFE DE OBRA",
                          metodo="parte_anterior",
                          origen="parte PT26/00319 · 09/2026 · obra 0694")


def test_f050_r1_paso1_solo_ese_recurso_y_esa_obra():
    hist = [_h(recurso=999), _h(obra=OTRA)]
    assert previa_en_obra(hist, RECURSO, OBRA, _hojas(_nodos())) is None


def test_f050_r2_paso1_gana_la_de_mas_can_sumado_en_el_mes():
    hist = [_h(can=0.3, parte="PT26/00319"),
            _h(can=0.3, parte="PT26/00400"),
            _h(can=0.5, paride=2108, cod="CI.1.8"),
            _h(mes=8, can=5.0, paride=2108, cod="CI.1.8")]
    p = previa_en_obra(hist, RECURSO, OBRA, _hojas(_nodos()))
    assert (p.paride, p.origen) == (
        2105, "parte PT26/00319, PT26/00400 · 09/2026 · obra 0694")


def test_f050_r2_paso1_empate_no_propone_nunca_la_primera():
    hist = [_h(can=0.5), _h(can=0.5, paride=2108, cod="CI.1.8")]
    assert previa_en_obra(hist, RECURSO, OBRA, _hojas(_nodos())) is None


def test_f050_r2_paso1_empate_por_redondeo_tambien_es_empate():
    hist = [_h(can=0.1), _h(can=0.2), _h(can=0.3, paride=2108, cod="CI.1.8")]
    assert previa_en_obra(hist, RECURSO, OBRA, _hojas(_nodos())) is None


def test_f050_r3_paso1_hoja_de_baja_o_capitulo_no_se_propone():
    nodos = _nodos()
    assert previa_en_obra([_h(paride=2111, cod="CI.1.11")], RECURSO, OBRA,
                          _hojas(nodos)) is None
    assert previa_en_obra([_h(paride=2100, cod="CI.1")], RECURSO, OBRA,
                          _hojas(nodos)) is None


def test_f050_r4_paso1_ignora_lineas_sin_partida():
    hist = [_h(can=0.9, paride=0, cod=None, res=None), _h(can=0.1)]
    assert previa_en_obra(hist, RECURSO, OBRA, _hojas(_nodos())).paride == 2105


# ============================ R1 · paso 2 ================================ #
def test_f050_r1_paso2_ultimo_parte_de_otra_obra_trasladado():
    hist = [_h(obra=OTRA, mes=8, paride=88001, cod="CI.1.9",
               res="Administrativo", parte="PT26/00200"),
            _h(obra=OTRA, mes=6, paride=88002, cod="CI.1.8",
               res="ENCARGADO (ACUNA)")]
    p = ultima_de_recurso(hist, RECURSO, OBRA, _hojas(_nodos()))
    assert p == Propuesta(paride=2109, cod="CI.1.9", res="ADMINISTRATIVO",
                          metodo="ultimo_parte",
                          origen="parte PT26/00200 · 08/2026 · obra 0696")


def test_f050_r1_paso2_no_mira_la_propia_obra():
    assert ultima_de_recurso([_h()], RECURSO, OBRA, _hojas(_nodos())) is None


def test_f050_r1_paso2_codigo_y_descripcion_iguales():
    nodos = _hojas(_nodos())
    solo_cod = [_h(obra=OTRA, paride=88001, cod="CI.1.9", res="OTRA COSA")]
    solo_res = [_h(obra=OTRA, paride=88001, cod="CI.9.9",
                   res="ADMINISTRATIVO")]
    assert ultima_de_recurso(solo_cod, RECURSO, OBRA, nodos) is None
    assert ultima_de_recurso(solo_res, RECURSO, OBRA, nodos) is None


def test_f050_r2_paso2_traslado_con_dos_hojas_no_propone():
    hist = [_h(obra=OTRA, paride=88001, cod="CI.2.1",
               res="OFICIAL (REMATES)")]
    nodos = _nodos([f for f in PRESUPUESTO if f["ide"] != 2301]
                   + [_fila(2301, 2300, 13, "CI.2.1", "OFICIAL (REMATES)")])
    assert ultima_de_recurso(hist, RECURSO, OBRA, _hojas(nodos)) is None


def test_f050_r2_paso2_traslado_sin_hoja_no_propone():
    hist = [_h(obra=OTRA, paride=88001, cod="CI.7.7", res="NADA")]
    assert ultima_de_recurso(hist, RECURSO, OBRA, _hojas(_nodos())) is None


def test_f050_r2_paso2_empate_en_el_mes_no_propone():
    hist = [_h(obra=OTRA, can=0.5, paride=88001, cod="CI.1.9",
               res="ADMINISTRATIVO"),
            _h(obra=697, can=0.5, paride=88002, cod="CI.1.8",
               res="ENCARGADO (ACUNA)")]
    assert ultima_de_recurso(hist, RECURSO, OBRA, _hojas(_nodos())) is None


def test_f050_r2_paso2_suma_por_codigo_y_descripcion_entre_obras():
    hist = [_h(obra=OTRA, can=0.3, paride=88001, cod="CI.1.9",
               res="ADMINISTRATIVO", parte="PT26/00500"),
            _h(obra=697, can=0.3, paride=77001, cod="ci.1.9",
               res="Administrativo", parte="PT26/00600", obra_cod="0697"),
            _h(obra=698, can=0.5, paride=66001, cod="CI.1.8",
               res="ENCARGADO (ACUNA)")]
    p = ultima_de_recurso(hist, RECURSO, OBRA, _hojas(_nodos()))
    assert (p.paride, p.origen) == (
        2109, "parte PT26/00500, PT26/00600 · 09/2026 · obra 0696, 0697")


def test_f050_r2_paso2_sin_codigo_ni_descripcion_no_traslada():
    filas = PRESUPUESTO + [_fila(2400, 2000, 20, None, None)]
    hist = [_h(obra=OTRA, paride=88001, cod=None, res=None)]
    assert ultima_de_recurso(hist, RECURSO, OBRA,
                             _hojas(_nodos(filas))) is None


# ======================= R1 · los tres pasos en orden ===================== #
def test_f050_r1_paso1_manda_sobre_paso2_y_casamiento():
    hist = [_h(mes=5), _h(obra=OTRA, mes=9, paride=88001, cod="CI.1.9",
                          res="ADMINISTRATIVO")]
    p = proponer_partida(_nodos(), hist, RECURSO, OBRA, "Encargado",
                         "Acuna Mera, Antonio")
    assert (p.paride, p.metodo) == (2105, "parte_anterior")


def test_f050_r1_sin_paso1_va_al_paso2():
    hist = [_h(obra=OTRA, paride=88001, cod="CI.1.9", res="ADMINISTRATIVO")]
    p = proponer_partida(_nodos(), hist, RECURSO, OBRA, "Encargado",
                         "Acuna Mera, Antonio")
    assert (p.paride, p.metodo) == (2109, "ultimo_parte")


def test_f050_r1_r3_sin_pasos_1_y_2_casamiento_de_hoy():
    hist = [_h(paride=2111, cod="CI.1.11")]           # de baja: se salta
    p = proponer_partida(_nodos(), hist, RECURSO, OBRA, "Encargado",
                         "Acuna Mera, Antonio")
    assert p == Propuesta(paride=2108, cod="CI.1.8",
                          res="ENCARGADO (ACUNA)", metodo="auto_nombre",
                          origen=None)
    p = proponer_partida(_nodos(), [], RECURSO, OBRA, "Topógrafo", "Nadie")
    assert (p.paride, p.metodo, p.origen) == (2110, "auto_categoria", None)


def test_f050_r1_nada_casa_sin_propuesta():
    assert proponer_partida(_nodos(), [], RECURSO, OBRA, "Astronauta",
                            "Nadie") is None


# ============================ R5 · el orden ============================== #
def test_f050_r5_filas_barajadas_misma_propuesta():
    hist = [_h(mes=9, can=0.3, parte="PT26/00319"),
            _h(mes=9, can=0.3, parte="PT26/00400"),
            _h(mes=9, can=0.5, paride=2108, cod="CI.1.8"),
            _h(mes=8, paride=2109, cod="CI.1.9"),
            _h(obra=OTRA, mes=10, paride=88001, cod="CI.1.10",
               res="TOPOGRAFO")]
    esperado = proponer_partida(_nodos(), hist, RECURSO, OBRA, None, None)
    filas = list(reversed(PRESUPUESTO))
    for semilla in range(20):
        barajado = hist[:]
        random.Random(semilla).shuffle(barajado)
        assert proponer_partida(_nodos(filas), barajado, RECURSO, OBRA, None,
                                None) == esperado
    assert esperado.origen == "parte PT26/00319, PT26/00400 · 09/2026 · " \
                              "obra 0694"


# ========================= R8 · mayor_inicial ============================ #
def test_f050_r8_mayor_inicial_de_la_propuesta():
    nodos = _nodos()
    prop = Propuesta(1002, "1.4.1.8", "COSTES INDIRECTOS DE ESTRUCTURA",
                     "parte_anterior", "x")
    assert mayor_inicial(prop, nodos, "Encargado") == "CD"
    prop_cp = Propuesta(3001, "CP.1", "SEGUROS", "ultimo_parte", "x")
    assert mayor_inicial(prop_cp, nodos, "Oficial") == "CP"


def test_f050_r8_mayor_inicial_sin_propuesta_ci_para_mando():
    nodos = _nodos()
    assert mayor_inicial(None, nodos, "Encargado") == "CI"
    assert mayor_inicial(None, nodos, "Jefe de grupo") == "CI"
    assert mayor_inicial(None, nodos, "Oficial 1ª") is None
    assert mayor_inicial(None, nodos, None) is None


def test_f050_r8_mayor_inicial_propuesta_fuera_del_presupuesto():
    prop = Propuesta(55, "X", "X", "postventa", None)
    assert mayor_inicial(prop, _nodos(), "Encargado") == "CI"
    assert mayor_inicial(prop, _nodos(), "Peón") is None


# ================== T2 · historial_partidas (R4, R7) ===================== #
class _ReadFalso:
    """`_read` del cliente: anota (sql, parámetros) y devuelve `filas`."""

    def __init__(self, filas=None) -> None:
        self.filas = list(filas or [])
        self.llamadas: list[tuple[str, list]] = []

    def __call__(self, sql, params):
        self.llamadas.append((" ".join(sql.split()), list(params)))
        return list(self.filas)


def _cliente_historial(filas=None, **kw):
    from infrastructure.sigrid.sigrid_write_client import SigridWriteClient
    cli = SigridWriteClient(base_url="http://sigrid.invalid",
                            function_key="sin-clave", database="ruesma", **kw)
    falso = _ReadFalso(filas)
    cli._read = falso
    return cli, falso


FILA_SIGRID = {"reside": 4321, "obride": 694, "obra_cod": "0694 ",
               "parte_cod": "PT26/00319", "ano": 2026, "mes": 9, "can": 0.4,
               "paride": 2105, "par_cod": " CI.1.5 ", "par_res": "JEFE DE OBRA"}


def test_f050_r4_historial_sql_con_los_filtros_de_la_regla():
    cli, falso = _cliente_historial(tip_parte=35)
    cli.historial_partidas([4321, 17, 4321], 202409, 202609)
    [(sql, params)] = falso.llamadas
    for trozo in ("FROM hmores h JOIN hmo m ON m.ide = h.hmoide",
                  "JOIN con c ON c.ide = m.ide",
                  "JOIN con co ON co.ide = m.obride",
                  "JOIN auxhor a ON a.ide = h.horide",
                  "JOIN obrparpar p ON p.ide = h.paride",
                  "h.reside IN (?,?)", "c.tip = ?", "a.cod LIKE 'M%'",
                  "p.obride = m.obride",
                  "(m.ano * 100 + m.mes) BETWEEN ? AND ?"):
        assert trozo in sql, trozo
    assert params == [17, 4321, 35, 202409, 202609]


def test_f050_r4_historial_tipo_de_parte_del_ajuste():
    cli, falso = _cliente_historial(tip_parte=99)
    cli.historial_partidas([1], 202401, 202402)
    assert falso.llamadas[0][1] == [1, 99, 202401, 202402]


def test_f050_r7_historial_lotes_de_500_recursos():
    cli, falso = _cliente_historial()
    cli.historial_partidas(range(1, 1201), 202409, 202609)
    assert [len(p) - 3 for _, p in falso.llamadas] == [500, 500, 200]
    assert falso.llamadas[1][1][:2] == [501, 502]


def test_f050_r7_historial_sin_recursos_no_lee():
    cli, falso = _cliente_historial()
    assert cli.historial_partidas([None, 0], 202409, 202609) == []
    assert falso.llamadas == []


def test_f050_r4_historial_mapea_las_filas():
    vacia = dict(FILA_SIGRID, obra_cod=None, parte_cod=None, can=None,
                 par_cod=None, par_res=None)
    cli, _ = _cliente_historial([FILA_SIGRID, vacia])
    assert cli.historial_partidas([4321], 202409, 202609) == [
        LineaHistorial(reside=4321, obride=694, obra_cod="0694",
                       parte_cod="PT26/00319", ano=2026, mes=9, can=0.4,
                       paride=2105, par_cod="CI.1.5", par_res="JEFE DE OBRA"),
        LineaHistorial(reside=4321, obride=694, obra_cod=None,
                       parte_cod=None, ano=2026, mes=9, can=0.0,
                       paride=2105, par_cod=None, par_res=None)]


def test_f050_r7_historial_truncado_es_error(monkeypatch):
    from tests.test_f047_tope_filas import _cliente, _emulada
    _emulada(monkeypatch, [dict(FILA_SIGRID), dict(FILA_SIGRID)])
    with pytest.raises(RuntimeError, match="truncada"):
        _cliente(max_rows=1).historial_partidas([4321], 202409, 202609)


def test_f050_r1_historial_ajuste_de_meses_atras(monkeypatch):
    from config.settings import Settings
    monkeypatch.setenv("SIGRID_API_BASE_URL", "http://sigrid.invalid")
    monkeypatch.setenv("SIGRID_API_FUNCTION_KEY", "sin-clave")
    monkeypatch.delenv("PROPUESTA_MESES_ATRAS", raising=False)
    assert Settings(_env_file=None).propuesta_meses_atras == 24
    monkeypatch.setenv("PROPUESTA_MESES_ATRAS", "6")
    assert Settings(_env_file=None).propuesta_meses_atras == 6


# ============ T15 · casos que la campaña de mutación dejó vivos ============ #
def test_f050_r5_las_propuestas_y_el_historial_son_inmutables():
    from dataclasses import FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        _h().can = 9.0
    with pytest.raises(FrozenInstanceError):
        Propuesta(1, "X", "Y", "manual").paride = 2


def test_f050_r2_diferencias_por_debajo_de_la_millonesima_son_empate():
    """`can` viaja con 4 decimales: lo que difiere menos de 1e-6 es ruido de
    coma flotante y empata; 1e-6 o más, no."""
    empate = [_h(can=0.3000004), _h(can=0.3, paride=2108, cod="CI.1.8")]
    assert previa_en_obra(empate, RECURSO, OBRA, _hojas(_nodos())) is None
    gana = [_h(can=0.300002), _h(can=0.3, paride=2108, cod="CI.1.8")]
    assert previa_en_obra(gana, RECURSO, OBRA, _hojas(_nodos())).paride \
        == 2105


def test_f050_r2_una_linea_sin_can_suma_cero():
    hojas = _hojas(_nodos())
    assert previa_en_obra([_h(can=None), _h(can=0.5, paride=2108,
                                            cod="CI.1.8")],
                          RECURSO, OBRA, hojas).paride == 2108
    otra = [_h(obra=OTRA, can=None, paride=1, cod="CI.1.5",
               res="JEFE DE OBRA"),
            _h(obra=OTRA, can=0.5, paride=2, cod="CI.1.9",
               res="ADMINISTRATIVO")]
    assert ultima_de_recurso(otra, RECURSO, OBRA, hojas).paride == 2109
