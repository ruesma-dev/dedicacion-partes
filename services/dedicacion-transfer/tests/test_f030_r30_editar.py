# tests/test_f030_r30_editar.py
"""F-030 · Anexo R30 en el transfer: cambiar los días de una incidencia ya
registrada EDITA la `fec` de sus líneas (R40-R46,
ARCHITECTURE.md#regla-incidencia).

- Contrato (T27): la incidencia trae la traza de la api (`hmores_ide_*`,
  `dia_*`, opcionales) y la acción `editar` publica `fec_antes`.
- Cliente (T28): la lectura de R33 trae `can`, parte y estado y busca
  también por `ide`; el `UPDATE` de la `fec` lleva la guarda de F-051.
- Reglas (T29): `reconciliar`, pura.
- Preflight, lote (T30) y `ejecutar` (T31).

Sin red ni BBDD: el cliente con su `_read` sustituido por un doble y el
pipeline con los dobles de `conftest.py`. Los `ide` son inventados.
"""
from __future__ import annotations

import pytest
from domain.models.registro_models import (
    AccionIncidencia,
    IncidenciaEntrada,
    LineaIncidenciaSigrid,
)

from tests.conftest import OBRA_ORIGEN
from tests.test_f030_pipeline_incidencias import (
    CLAVES_INC,
    ClienteInc,
    _json_inc,
    _json_linea,
)

TRAZA = {"hmores_ide_ini": 9001, "hmores_ide_fin": 9002, "dia_ini": 5,
         "dia_fin": 9}


@pytest.fixture
def api(monkeypatch):
    """La app real con el cliente que se le dé (como la de
    `test_f030_pipeline_incidencias`)."""
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from interface_adapters.api import app as modulo_app

    from tests.test_f050_endpoint_propuesta import AJUSTES

    def fabricar(cli, **ajustes):
        monkeypatch.setattr(modulo_app, "SigridWriteClient", lambda **kw: cli)
        st = SimpleNamespace(**{**AJUSTES, "sigrid_lecturas_paralelas": 4,
                                **ajustes})
        return TestClient(modulo_app.build_app(st))
    return fabricar


# ============================ contrato (T27) ============================ #
def test_f030_r30_contrato_entrada_con_la_traza_opcional():
    from interface_adapters.api.app import IncidenciaIn

    sin = IncidenciaEntrada(id=7, recurso_ide=200, empresa=1, codigo="CIV",
                            ano=2026, mes=7, desde=5, hasta=9)
    assert (sin.hmores_ide_ini, sin.hmores_ide_fin, sin.dia_ini,
            sin.dia_fin) == (None,) * 4
    entrada = IncidenciaEntrada(**IncidenciaIn(**_json_inc(**TRAZA)).model_dump())
    assert (entrada.hmores_ide_ini, entrada.hmores_ide_fin, entrada.dia_ini,
            entrada.dia_fin) == (9001, 9002, 5, 9)
    assert IncidenciaIn(**_json_inc()).hmores_ide_ini is None


def test_f030_r30_contrato_accion_y_linea_con_los_campos_nuevos():
    a = AccionIncidencia(id=7, rol="ini", accion="editar", fecha_int=20260706)
    assert (a.fec_antes, a.hmoide) == (None, None)
    ls = LineaIncidenciaSigrid(51, 200, 20260705, "CIV", "porcentajes:inc:7:ini",
                               "PT26/1")
    assert (ls.can, ls.hmoide, ls.parte_est) == (None, None, None)


def test_f030_r46_contrato_solo_editar_publica_fec_antes():
    from interface_adapters.api.app import _con_incidencias

    editar = AccionIncidencia(id=7, rol="ini", accion="editar",
                              fecha_int=20260706, fec_antes=20260705,
                              hmores_ide=9001, hmoide=777)
    ya = AccionIncidencia(id=7, rol="fin", accion="ya_registrado",
                          fecha_int=20260709, hmores_ide=9002)
    r = _con_incidencias({}, [editar, ya])
    assert set(r["incidencias"][0]) == CLAVES_INC | {"fec_antes"}
    assert r["incidencias"][0]["fec_antes"] == 20260705
    assert set(r["incidencias"][1]) == CLAVES_INC
    assert "hmoide" not in r["incidencias"][0]          # interno


def test_f030_r30_contrato_sin_los_campos_responde_igual(api):
    peticion = {"obra": {"codigo": OBRA_ORIGEN}, "lineas": [_json_linea(1)],
                "incidencias": [_json_inc()]}
    hoy = api(ClienteInc()).post("/api/registro/preflight",
                                 json=peticion).json()
    nulos = api(ClienteInc()).post("/api/registro/preflight", json={
        **peticion, "incidencias": [_json_inc(
            hmores_ide_ini=None, hmores_ide_fin=None, dia_ini=None,
            dia_fin=None)]}).json()
    assert nulos == hoy and hoy["ok"] is True
    assert [set(x) for x in hoy["incidencias"]] == [CLAVES_INC] * 2


# ============================ cliente (T28) ============================= #
from tests.test_f050_propuesta import _cliente_historial

FILA = {"ide": 9001, "reside": 200, "fec": 20260705, "cod": "CIV ",
        "synckey": " porcentajes:inc:7:ini ", "parte": " PT26/1 ", "can": 0,
        "hmoide": 777, "est": 1}
SELECT = ("SELECT h.ide AS ide, h.reside AS reside, h.fec AS fec, "
          "a.cod AS cod, h.synckey AS synckey, c.cod AS parte, "
          "h.can AS can, h.hmoide AS hmoide, c.est AS est FROM hmores h "
          "JOIN auxhor a ON a.ide = h.horide JOIN hmo m ON m.ide = h.hmoide "
          "JOIN con c ON c.ide = m.ide ")
GUARDA_INC = (
    "WHERE ide = ? AND reside = ? AND ABS(ISNULL(can, 0) - ?) < 0.000001 "
    "AND LTRIM(RTRIM(ISNULL(synckey, ''))) = ? "
    "AND ISNULL(dvaproide, 0) = 0 AND ISNULL(dvfproide, 0) = 0 "
    "AND ISNULL(hdereside, 0) = 0 AND ISNULL(empdpreide, 0) = 0 "
    "AND ISNULL(empabside, 0) = 0 AND ISNULL(emprccide, 0) = 0 "
    "AND EXISTS (SELECT 1 FROM auxhor a WHERE a.ide = hmores.horide "
    "AND a.cod = ?) "
    "AND EXISTS (SELECT 1 FROM con c WHERE c.ide = hmores.hmoide "
    "AND c.est = ?)")


def test_f030_r40_sql_por_recurso_o_por_ide_con_can_parte_y_estado():
    cli, falso = _cliente_historial([
        FILA, dict(FILA, ide=9002, can=None, hmoide=None, est=None,
                   cod="CIP")])
    filas = cli.incidencias_del_mes([300, 200], 2026, 7, ides=[9002, None,
                                                                 9001, 9001])
    [(sql, params)] = falso.llamadas
    assert sql == SELECT + (
        "WHERE (h.reside IN (?,?) AND h.fec BETWEEN ? AND ? "
        "AND a.cod LIKE ? OR h.ide IN (?,?)) ORDER BY h.ide")
    assert params == [200, 300, 20260701, 20260731, "CI%", 9001, 9002]
    assert filas == [
        LineaIncidenciaSigrid(9001, 200, 20260705, "CIV",
                              "porcentajes:inc:7:ini", "PT26/1", can=0.0,
                              hmoide=777, parte_est=1),
        LineaIncidenciaSigrid(9002, 200, 20260705, "CIP",
                              "porcentajes:inc:7:ini", "PT26/1", can=None,
                              hmoide=None, parte_est=None)]
    assert isinstance(filas[0].can, float)


def test_f030_r40_sql_sin_ides_el_where_de_hoy():
    cli, falso = _cliente_historial()
    cli.incidencias_del_mes([200], 2026, 7)
    [(sql, params)] = falso.llamadas
    assert sql == SELECT + (
        "WHERE h.reside IN (?) AND h.fec BETWEEN ? AND ? "
        "AND a.cod LIKE ? ORDER BY h.ide")
    assert params == [200, 20260701, 20260731, "CI%"]


def test_f030_r40_sql_en_pruebas_el_filtro_de_partes_a_todo():
    cli, falso = _cliente_historial()
    cli.incidencias_del_mes([200], 2026, 7, hmoides=[12, 11], ides=[9001])
    [(sql, params)] = falso.llamadas
    assert sql.endswith("a.cod LIKE ? OR h.ide IN (?)) "
                        "AND h.hmoide IN (?,?) ORDER BY h.ide")
    assert params == [200, 20260701, 20260731, "CI%", 9001, 11, 12]
    cli, falso = _cliente_historial()
    assert cli.incidencias_del_mes([200], 2026, 7, hmoides=[],
                                   ides=[9001]) == []
    assert falso.llamadas == []


def test_f030_r40_sql_solo_ides_y_trozos_sin_repetir():
    cli, falso = _cliente_historial()
    cli.incidencias_del_mes([None], 2026, 7, ides=[9001])
    [(sql, params)] = falso.llamadas
    assert sql == SELECT + "WHERE (h.ide IN (?)) ORDER BY h.ide"
    assert params == [9001]
    # 600 recursos y 2 `ide`: 500 recursos y luego 100 más los 2 `ide`; la
    # línea que sale en los dos trozos, una vez.
    cli, falso = _cliente_historial([FILA])
    filas = cli.incidencias_del_mes(range(1, 601), 2026, 7, ides=[9001, 9002])
    assert [len(p) for _, p in falso.llamadas] == [503, 105]
    assert falso.llamadas[1][1][-2:] == [9001, 9002]
    assert "OR h.ide IN" not in falso.llamadas[0][0]
    assert [f.ide for f in filas] == [9001]


def test_f030_r41_sql_editar_la_fec_con_la_guarda_de_su_codigo():
    cli, _ = _cliente_historial()
    st = cli.stmt_editar_fecha_incidencia(
        ide=9001, reside=200, hora_codigo="CIV", synckey_leida=" k ",
        fecha_int=20260706)
    assert " ".join(st["sql"].split()) == "UPDATE hmores SET fec = ? " + GUARDA_INC
    assert st["parameters"] == [20260706, 9001, 200, 0.0, "k", "CIV", 1]
    sin_sk = cli.stmt_editar_fecha_incidencia(
        ide="9002", reside="200", hora_codigo=" CIZ ", synckey_leida=None,
        fecha_int="20260712")
    assert sin_sk["parameters"] == [20260712, 9002, 200, 0.0, "", "CIZ", 1]


def test_f030_r41_sql_la_guarda_sin_codigo_es_la_de_f051():
    cli, _ = _cliente_historial()
    assert cli._guarda(1, 2, 0.5, "k") == cli._guarda(1, 2, 0.5, "k", None)
    texto, params = cli._guarda(1, 2, 0.5, "k", "CIV")
    assert "a.cod = ?" in texto and "LIKE 'M%'" not in texto
    assert params == [1, 2, 0.5, "k", "CIV", 1]
