# tests/test_f055_validar_partidas.py
"""F-055 · T3: `validar_partidas` (R3, R4; design §5.1 y §6).

Valida unas partidas por `ide` en UNA lectura (trozos de 500): su obra, si
son hoja (sin hijas de la misma obra, como `build_arbol_partidas`) y si
están de alta (`tipdes = 0`). R4: el veredicto «vale en la obra de origen»
(`obride == origen and es_hoja and activa`) es el mismo que da hoy el
presupuesto entero (`construir_catalogo`) en hoja activa, capítulo, baja,
otra obra e inexistente. El `ClienteFalso` de `conftest.py` lo deriva de sus
presupuestos, sin leer ninguno.

Sin red ni BBDD; `_read` sustituido por un doble. Los `ide` son inventados.
"""
from __future__ import annotations

import pytest
from application.services.partida_resolver import construir_catalogo
from domain.models.registro_models import PartidaValida
from infrastructure.sigrid.sigrid_write_client import (
    LOTE_PARAMETROS,
    SigridWriteClient,
    medir_lecturas,
)

from tests.conftest import (
    PRESUPUESTO_ORIGEN,
    PRESUPUESTO_PV_HOJAS,
    ClienteFalso,
    _fila,
)
from tests.test_f050_propuesta import _cliente_historial

ORIGEN = 555001
OTRA = 777001

#: Presupuestos de dos obras: en la de origen hay hoja activa, capítulo,
#: hoja de baja y un capítulo de baja; en la otra, una hoja activa y un
#: «capítulo» cuya hija es de OTRA obra (para la obra suya, es hoja).
FILAS = {
    ORIGEN: [
        _fila(80000, 0, 0, "CI", "COSTES INDIRECTOS"),
        _fila(80001, 80000, 1, "CI.1.10", "ENCARGADO (ACUNA)"),
        _fila(80004, 80000, 2, "CI.1.8", "VIGILANTE", tipdes=1),
        _fila(80010, 80000, 3, "CI.2", "VARIOS", tipdes=2),
        _fila(80011, 80010, 1, "CI.2.1", "OFICIAL"),
        _fila(80020, 0, 4, "CD", "DIRECTOS"),
    ],
    OTRA: [
        _fila(90000, 0, 0, "CI", "COSTES INDIRECTOS"),
        _fila(90001, 90000, 1, "CI.1", "JEFE DE OBRA"),
    ],
}
#: Una fila de la otra obra que cuelga de la raíz `CD` de la de origen.
#: En Sigrid no debería pasar; si pasa, `CD` sigue siendo hoja para su obra.
INTRUSA = dict(_fila(90002, 80020, 2, "CI.2", "INTRUSA"))


def _sigrid_emulada(sql: str, params: list) -> list[dict]:
    """Lo que devolvería Sigrid a la consulta de §6, calculado aquí sobre
    `FILAS` (hoja = sin hijas de su MISMA obra; `tipdes` con `ISNULL`)."""
    assert "FROM obrparpar p WHERE p.ide IN (" in " ".join(sql.split())
    todas = [(o, f) for o, filas in FILAS.items() for f in filas]
    todas.append((OTRA, INTRUSA))
    out = []
    for obride, f in todas:
        if f["ide"] not in params:
            continue
        hijas = [1 for o2, h in todas
                 if h["padide"] == f["ide"] and o2 == obride]
        out.append({"ide": f["ide"], "obride": obride, "cod": f["cod"],
                    "res": f["res"], "tipdes": f["tipdes"] or 0,
                    "hoja": 0 if hijas else 1})
    return out


def _cliente() -> SigridWriteClient:
    cli = SigridWriteClient(base_url="http://sigrid.invalid",
                            function_key="sin-clave", database="ruesma")
    cli._read = _sigrid_emulada              # type: ignore[method-assign]
    return cli


# ============================ SQL y lectura ============================ #
def test_f055_r3_sql_de_la_validacion_por_ide():
    cli, falso = _cliente_historial()
    cli.validar_partidas([80002, 80001, 80002, None, 0])
    [(sql, params)] = falso.llamadas
    for trozo in (
            "SELECT p.ide AS ide, p.obride AS obride, p.cod AS cod, "
            "p.res AS res, ISNULL(p.tipdes,0) AS tipdes",
            "CASE WHEN EXISTS (SELECT 1 FROM obrparpar h WHERE "
            "h.padide = p.ide AND h.obride = p.obride) THEN 0 ELSE 1 END "
            "AS hoja",
            "FROM obrparpar p WHERE p.ide IN (?,?)"):
        assert trozo in sql, trozo
    assert params == [80001, 80002]


def test_f055_r3_sin_partidas_no_lee():
    cli, falso = _cliente_historial()
    assert cli.validar_partidas([None, 0]) == {}
    assert cli.validar_partidas([]) == {}
    assert falso.llamadas == []


def test_f055_r3_trozos_de_500():
    cli, falso = _cliente_historial()
    cli.validar_partidas(range(1, 1102))
    assert LOTE_PARAMETROS == 500
    assert [len(p) for _, p in falso.llamadas] == [500, 500, 101]
    assert falso.llamadas[1][1][0] == 501


def test_f055_r3_mapea_las_filas():
    cli, _ = _cliente_historial([
        {"ide": 7, "obride": 3, "cod": "CI.1", "res": "JEFE", "tipdes": 0,
         "hoja": 1},
        {"ide": 8, "obride": 3, "cod": None, "res": None, "tipdes": 1,
         "hoja": 0}])
    assert cli.validar_partidas([7, 8]) == {
        7: PartidaValida(ide=7, obride=3, cod="CI.1", res="JEFE",
                         es_hoja=True, activa=True),
        8: PartidaValida(ide=8, obride=3, cod=None, res=None, es_hoja=False,
                         activa=False)}


def test_f055_r3_una_lectura_medida_con_su_nombre():
    with medir_lecturas() as m:
        _cliente().validar_partidas([80001, 90001])
    assert [(l.nombre, l.filas) for l in m.lecturas] == [
        ("validar_partidas", 2)]


def test_f055_r3_truncado_es_error(monkeypatch):
    from tests.test_f047_tope_filas import _cliente as cliente_emulado
    from tests.test_f047_tope_filas import _emulada
    fila = {"ide": 1, "obride": 2, "cod": "X", "res": "Y", "tipdes": 0,
            "hoja": 1}
    _emulada(monkeypatch, [dict(fila), dict(fila, ide=3)])
    with pytest.raises(RuntimeError, match="truncada"):
        cliente_emulado(max_rows=1).validar_partidas([1, 3])


def test_f055_r3_partida_valida_es_inmutable():
    from dataclasses import FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        PartidaValida(1, 2, "A", "B", True, True).activa = False


# ===================== R4 · mismo veredicto que hoy ===================== #
CASOS_R4 = {
    80001: "hoja activa",
    80004: "hoja de baja",
    80000: "capítulo",
    80010: "capítulo de baja",
    80011: "hoja activa bajo capítulo de baja",
    80020: "raíz con hija de otra obra (hoja para su obra)",
    90001: "hoja activa de otra obra",
    12345: "inexistente",
}


@pytest.mark.parametrize("paride", sorted(CASOS_R4), ids=CASOS_R4.get)
def test_f055_r4_mismo_veredicto_que_construir_catalogo(paride):
    nodos = construir_catalogo(FILAS[ORIGEN])
    nodo = nodos.get(paride)
    hoy = bool(nodo and nodo.es_hoja and nodo.activa)
    validas = _cliente().validar_partidas([paride])
    v = validas.get(paride)
    assert (v is not None and v.vale_en(ORIGEN)) is hoy


def test_f055_r4_vale_en_exige_obra_hoja_y_alta():
    assert PartidaValida(1, ORIGEN, "A", "B", True, True).vale_en(ORIGEN)
    assert not PartidaValida(1, OTRA, "A", "B", True, True).vale_en(ORIGEN)
    assert not PartidaValida(1, ORIGEN, "A", "B", False, True).vale_en(
        ORIGEN)
    assert not PartidaValida(1, ORIGEN, "A", "B", True, False).vale_en(
        ORIGEN)


# =================== el doble de `conftest.py` (T3) ===================== #
def test_f055_r4_el_doble_deriva_de_sus_presupuestos_sin_leerlos():
    cli = ClienteFalso()
    ides = [f["ide"] for f in PRESUPUESTO_ORIGEN + PRESUPUESTO_PV_HOJAS]
    validas = cli.validar_partidas(ides + [12345])
    assert cli.n_capitulos_de_obra == 0
    assert cli.validadas == [sorted(set(ides + [12345]))]
    for obride, filas in ((cli.obra_origen.ide, PRESUPUESTO_ORIGEN),
                          (cli.obra_pv.ide, PRESUPUESTO_PV_HOJAS)):
        nodos = construir_catalogo(filas)
        for f in filas:
            v = validas[f["ide"]]
            n = nodos[f["ide"]]
            assert (v.obride, v.cod, v.res, v.es_hoja, v.activa) == (
                obride, n.cod, n.res, n.es_hoja, n.activa)
    assert 12345 not in validas
    assert cli.validar_partidas([None, 0]) == {}
    assert len(cli.validadas) == 1              # sin partidas no «lee»


def test_f055_r4_el_doble_sigue_a_su_presupuesto_de_origen():
    """Un test que cambia `partidas_origen` cambia también la validación."""
    cli = ClienteFalso()
    cli.partidas_origen = [_fila(1, 0, 0, "CI.9", "SUELTA")]
    assert cli.validar_partidas([1, 80001]) == {
        1: PartidaValida(1, cli.obra_origen.ide, "CI.9", "SUELTA", True,
                         True)}
