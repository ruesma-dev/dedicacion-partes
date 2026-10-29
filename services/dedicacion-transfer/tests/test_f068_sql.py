# tests/test_f068_sql.py
"""F-068 · la lectura del historial de los vinculados (design §7; R11, R13).

`SigridWriteClient.historial_de_vinculados(resides, obra_ide, desde,
hasta)`: las líneas de partes de trabajo de esos recursos EN LA OBRA de
origen, en la ventana, con partida del presupuesto de esa obra y de
CUALQUIER hora (sin `auxhor` ni `LIKE 'M%'`); lotes de
`LOTE_RECURSOS_HISTORIAL`; sin recursos no lee; `truncated` es error. La SQL
de `historial_partidas` no cambia (sus tests de F-050 siguen).

Sin red ni BBDD: `_read` sustituido por un doble o la sigrid-api emulada.
"""
from __future__ import annotations

import pytest
from application.services.propuesta_partida import LineaHistorial
from infrastructure.sigrid.sigrid_write_client import (
    LOTE_RECURSOS_HISTORIAL,
    medir_lecturas,
)

from tests.test_f050_propuesta import FILA_SIGRID, _cliente_historial

SQL = (
    "SELECT h.reside AS reside, m.obride AS obride, co.cod AS obra_cod, "
    "c.cod AS parte_cod, m.ano AS ano, m.mes AS mes, h.can AS can, "
    "h.paride AS paride, p.cod AS par_cod, p.res AS par_res "
    "FROM hmores h JOIN hmo m ON m.ide = h.hmoide "
    "JOIN con c ON c.ide = m.ide JOIN con co ON co.ide = m.obride "
    "JOIN obrparpar p ON p.ide = h.paride "
    "WHERE h.reside IN ({marcas}) AND m.obride = ? AND c.tip = ? "
    "AND p.obride = m.obride AND (m.ano * 100 + m.mes) BETWEEN ? AND ?")


def test_f068_r11_sql_exacta_y_parametros():
    cli, falso = _cliente_historial(tip_parte=35)
    cli.historial_de_vinculados([12, 10, 12], 678000, 202410, 202610)
    [(sql, params)] = falso.llamadas
    assert sql == SQL.format(marcas="?,?")
    assert params == [10, 12, 678000, 35, 202410, 202610]


def test_f068_r11_cualquier_hora_y_solo_la_obra_de_origen():
    cli, falso = _cliente_historial()
    cli.historial_de_vinculados([10], 678000, 202410, 202610)
    [(sql, _)] = falso.llamadas
    assert "auxhor" not in sql and "LIKE" not in sql
    assert "m.obride = ?" in sql


def test_f068_r11_tipo_de_parte_del_ajuste():
    cli, falso = _cliente_historial(tip_parte=99)
    cli.historial_de_vinculados([1], "5", 202401, "202402")
    assert falso.llamadas[0][1] == [1, 5, 99, 202401, 202402]


def test_f068_r11_lotes_de_recursos():
    cli, falso = _cliente_historial()
    n = LOTE_RECURSOS_HISTORIAL * 2 + 200
    cli.historial_de_vinculados(range(1, n + 1), 678000, 202410, 202610)
    assert [len(p) - 4 for _, p in falso.llamadas] == [
        LOTE_RECURSOS_HISTORIAL, LOTE_RECURSOS_HISTORIAL, 200]
    segundo = falso.llamadas[1][1]
    assert segundo[:2] == [LOTE_RECURSOS_HISTORIAL + 1,
                           LOTE_RECURSOS_HISTORIAL + 2]
    assert segundo[-4:] == [678000, 35, 202410, 202610]
    assert all(s == SQL.format(marcas=",".join(
        "?" for _ in range(len(p) - 4))) for s, p in falso.llamadas)


def test_f068_r11_sin_recursos_no_lee():
    cli, falso = _cliente_historial()
    assert cli.historial_de_vinculados([None, 0], 678000, 202410,
                                       202610) == []
    assert cli.historial_de_vinculados([], 678000, 202410, 202610) == []
    assert falso.llamadas == []


def test_f068_r11_mapea_las_filas_como_el_historial_del_trabajador():
    vacia = dict(FILA_SIGRID, obra_cod=None, parte_cod=None, can=None,
                 par_cod=None, par_res=None)
    texto = dict(FILA_SIGRID, reside="4321", obride="694", ano="2026",
                 mes="9", paride="2105", can="0.5")
    cli, _ = _cliente_historial([FILA_SIGRID, vacia, texto])
    assert cli.historial_de_vinculados([4321], 694, 202409, 202609) == [
        LineaHistorial(reside=4321, obride=694, obra_cod="0694",
                       parte_cod="PT26/00319", ano=2026, mes=9, can=0.4,
                       paride=2105, par_cod="CI.1.5", par_res="JEFE DE OBRA"),
        LineaHistorial(reside=4321, obride=694, obra_cod=None,
                       parte_cod=None, ano=2026, mes=9, can=0.0,
                       paride=2105, par_cod=None, par_res=None),
        LineaHistorial(reside=4321, obride=694, obra_cod="0694",
                       parte_cod="PT26/00319", ano=2026, mes=9, can=0.5,
                       paride=2105, par_cod="CI.1.5", par_res="JEFE DE OBRA")]


def test_f068_r11_el_mismo_mapeo_que_historial_partidas():
    """`_linea_historial` lo usan los dos: misma fila, misma línea."""
    cli, _ = _cliente_historial([FILA_SIGRID])
    assert cli.historial_de_vinculados([4321], 694, 202409, 202609) == \
        cli.historial_partidas([4321], 202409, 202609)


def test_f068_r11_una_lectura_medida_con_su_nombre():
    cli, _ = _cliente_historial([FILA_SIGRID])
    with medir_lecturas() as m:
        cli.historial_de_vinculados([4321], 694, 202409, 202609)
    assert [(l.nombre, l.filas) for l in m.lecturas] == [
        ("historial_de_vinculados", 1)]


def test_f068_r13_truncado_es_error(monkeypatch):
    from tests.test_f047_tope_filas import _cliente, _emulada
    _emulada(monkeypatch, [dict(FILA_SIGRID), dict(FILA_SIGRID)])
    with pytest.raises(RuntimeError, match="truncada"):
        _cliente(max_rows=1).historial_de_vinculados([4321], 694, 202409,
                                                     202609)


def test_f068_r13_un_fallo_sube():
    cli, _ = _cliente_historial()

    def falla(sql, params):
        raise RuntimeError("sigrid-api read HTTP 502")

    cli._read = falla
    with pytest.raises(RuntimeError, match="502"):
        cli.historial_de_vinculados([10], 678000, 202410, 202610)
