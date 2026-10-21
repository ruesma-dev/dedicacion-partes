# tests/test_f030_pipeline_incidencias.py
"""F-030 · Las incidencias en el registro: cliente, pipeline, lote, contrato
y script (R23-R33, R35; ARCHITECTURE.md#regla-incidencia).

Sin red ni BBDD: el cliente de Sigrid con su `_read` sustituido por un doble
y el pipeline con el `ClienteFalso` de `conftest.py`. Los `ide` son
inventados y no coinciden con ningún dato real.
"""
from __future__ import annotations

import pytest

from tests.test_f050_propuesta import _cliente_historial


# ============================ cliente (T12) ============================== #
FILA_INC = {"ide": 900, "reside": 200, "fec": 20260705, "cod": "CIV ",
            "synckey": " porcentajes:inc:7:ini ", "parte": "PT26/00012"}


def test_f030_r27_cliente_sql_parametros_y_mapeo():
    from domain.models.registro_models import LineaIncidenciaSigrid

    cli, falso = _cliente_historial([FILA_INC, dict(FILA_INC, ide=901, synckey=None,
                                                    cod=None, parte=None)])
    filas = cli.incidencias_del_mes([300, 200, 300, None, 0], 2026, 2)
    [(sql, params)] = falso.llamadas
    assert sql == (
        "SELECT h.ide AS ide, h.reside AS reside, h.fec AS fec, a.cod AS cod, "
        "h.synckey AS synckey, c.cod AS parte FROM hmores h "
        "JOIN auxhor a ON a.ide = h.horide JOIN hmo m ON m.ide = h.hmoide "
        "JOIN con c ON c.ide = m.ide WHERE h.reside IN (?,?) "
        "AND h.fec BETWEEN ? AND ? AND a.cod LIKE ? ORDER BY h.ide")
    assert params == [200, 300, 20260201, 20260228, "CI%"]
    assert filas == [
        LineaIncidenciaSigrid(ide=900, reside=200, fecha_int=20260705,
                              hora_codigo="CIV", synckey="porcentajes:inc:7:ini",
                              parte_cod="PT26/00012"),
        LineaIncidenciaSigrid(ide=901, reside=200, fecha_int=20260705,
                              hora_codigo=None, synckey=None, parte_cod=None)]


def test_f030_r27_cliente_en_pruebas_solo_los_partes_dados():
    cli, falso = _cliente_historial()
    cli.incidencias_del_mes([200], 2026, 7, hmoides=[12, 11, 12])
    [(sql, params)] = falso.llamadas
    assert sql.endswith("AND a.cod LIKE ? AND h.hmoide IN (?,?) ORDER BY h.ide")
    assert params == [200, 20260701, 20260731, "CI%", 11, 12]


def test_f030_r33_cliente_sin_recursos_o_sin_partes_no_lee():
    cli, falso = _cliente_historial([FILA_INC])
    assert cli.incidencias_del_mes([None, 0], 2026, 7) == []
    assert cli.incidencias_del_mes([200], 2026, 7, hmoides=[]) == []
    assert cli.incidencias_del_mes([200], 2026, 7, hmoides=[0, None]) == []
    assert falso.llamadas == []


def test_f030_r33_cliente_en_trozos_de_500_recursos():
    cli, falso = _cliente_historial([FILA_INC])
    filas = cli.incidencias_del_mes(range(1, 1202), 2026, 7)
    assert [len(p) for _, p in falso.llamadas] == [503, 503, 204]   # + 3 fijos
    assert [p[0] for _, p in falso.llamadas] == [1, 501, 1001]
    assert len(filas) == 3
    cli, falso = _cliente_historial()
    cli.incidencias_del_mes(range(1, 501), 2026, 7)
    assert len(falso.llamadas) == 1


def test_f030_r33_cliente_truncado_es_error(monkeypatch):
    from tests.test_f047_tope_filas import _cliente as cliente_emulado
    from tests.test_f047_tope_filas import _emulada

    _emulada(monkeypatch, [dict(FILA_INC), dict(FILA_INC, ide=99)])
    with pytest.raises(RuntimeError, match="truncada"):
        cliente_emulado(max_rows=1).incidencias_del_mes([200], 2026, 7)


def test_f030_r33_cliente_se_mide_con_su_nombre():
    from infrastructure.sigrid.sigrid_write_client import medir_lecturas

    cli, _ = _cliente_historial()
    with medir_lecturas() as m:
        cli.incidencias_del_mes([1], 2026, 7)
    assert [l.nombre for l in m.lecturas] == ["incidencias_del_mes"]
