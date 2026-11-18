# tests/test_f054_lectura_mensuales.py
"""F-054 · T1: la lectura de las líneas mensuales del periodo (R4, R6;
design §4.1).

`SigridWriteClient.lineas_mensuales_del_periodo(empresa, ano, mes,
resides=None, solo_m=True)`: las líneas `hmores` con `can` ≠ 0 de los
partes de trabajo de obra (`con.tip` del ajuste, `hmo.reside` 0) del
periodo en obras de la empresa; `solo_m` añade `LIKE 'M%'`; con `resides`,
el `IN` en trozos de `LOTE_PARAMETROS`, una lectura por trozo. Cada fila,
una `LineaMensualSigrid` con su parte y si está En registro; `synckey`
vacía, `None`; `truncated` u `ok=false`, excepción.

Sin red ni BBDD: `_read` sustituido por un doble o la sigrid-api emulada.
"""
from __future__ import annotations

import pytest
from domain.models.registro_models import LineaMensualSigrid
from infrastructure.sigrid.sigrid_write_client import (
    LOTE_PARAMETROS,
    medir_lecturas,
)

from tests.test_f050_propuesta import _cliente_historial

BASE = (
    "SELECT h.ide AS ide, h.reside AS reside, m.obride AS obride, "
    "co.cod AS obra_cod, m.ide AS parte_ide, c.cod AS parte_cod, "
    "c.est AS parte_est, a.cod AS hora, h.can AS can, h.fec AS fec, "
    "h.paride AS paride, p.cod AS par_cod, p.res AS par_res, "
    "h.synckey AS synckey "
    "FROM hmores h JOIN hmo m ON m.ide = h.hmoide JOIN con c ON c.ide = m.ide "
    "JOIN con co ON co.ide = m.obride JOIN auxhor a ON a.ide = h.horide "
    "LEFT JOIN obrparpar p ON p.ide = h.paride "
    "WHERE c.tip = ? AND ISNULL(m.reside, 0) = 0 AND m.ano = ? AND m.mes = ? "
    "AND co.emp = ? AND ISNULL(h.can, 0) <> 0")

FILA = {"ide": 9001, "reside": 4321, "obride": 694, "obra_cod": "0694 ",
        "parte_ide": 777, "parte_cod": " PT26/00319", "parte_est": 1,
        "hora": "MADM ", "can": 0.95, "fec": 20260930, "paride": 2105,
        "par_cod": " CI.1.5 ", "par_res": "JEFE DE OBRA", "synckey": None}


def test_f054_r4_sql_exacta_con_solo_m_y_parametros_en_orden():
    cli, falso = _cliente_historial(tip_parte=35)
    cli.lineas_mensuales_del_periodo(1, 2026, 9)
    [(sql, params)] = falso.llamadas
    assert sql == BASE + " AND a.cod LIKE 'M%' ORDER BY h.ide"
    assert params == [35, 2026, 9, 1]


def test_f054_r4_solo_m_false_sin_el_like():
    cli, falso = _cliente_historial(tip_parte=35)
    cli.lineas_mensuales_del_periodo(2, 2026, 11, solo_m=False)
    [(sql, params)] = falso.llamadas
    assert sql == BASE + " ORDER BY h.ide"
    assert "LIKE" not in sql
    assert params == [35, 2026, 11, 2]


def test_f054_r4_tipo_de_parte_y_valores_como_entero():
    cli, falso = _cliente_historial(tip_parte=99)
    cli.lineas_mensuales_del_periodo("3", "2025", "1")
    assert falso.llamadas[0][1] == [99, 2025, 1, 3]


def test_f054_r4_con_recursos_el_in_en_trozos():
    cli, falso = _cliente_historial(tip_parte=35)
    n = LOTE_PARAMETROS * 2 + 7
    cli.lineas_mensuales_del_periodo(1, 2026, 9,
                                     resides=[*range(n, 0, -1), 5, None, 0])
    assert [len(p) - 4 for _, p in falso.llamadas] == [
        LOTE_PARAMETROS, LOTE_PARAMETROS, 7]
    for sql, params in falso.llamadas:
        marcas = ",".join("?" for _ in params[4:])
        assert sql == (BASE + " AND a.cod LIKE 'M%' AND h.reside IN ("
                       + marcas + ") ORDER BY h.ide")
        assert params[:4] == [35, 2026, 9, 1]
    assert falso.llamadas[0][1][4:6] == [1, 2]
    assert falso.llamadas[1][1][4] == LOTE_PARAMETROS + 1
    assert falso.llamadas[2][1][-1] == n


def test_f054_r4_recursos_sin_like_si_no_es_solo_m():
    cli, falso = _cliente_historial(tip_parte=35)
    cli.lineas_mensuales_del_periodo(1, 2026, 9, resides=[8, 3],
                                     solo_m=False)
    [(sql, params)] = falso.llamadas
    assert sql == BASE + " AND h.reside IN (?,?) ORDER BY h.ide"
    assert params == [35, 2026, 9, 1, 3, 8]


def test_f054_r4_recursos_vacios_no_lee():
    cli, falso = _cliente_historial()
    assert cli.lineas_mensuales_del_periodo(1, 2026, 9, resides=[]) == []
    assert cli.lineas_mensuales_del_periodo(1, 2026, 9,
                                            resides=[None, 0]) == []
    assert falso.llamadas == []


def test_f054_r6_mapea_la_fila_con_su_parte():
    cli, _ = _cliente_historial([FILA])
    assert cli.lineas_mensuales_del_periodo(1, 2026, 9) == [
        LineaMensualSigrid(
            hmores_ide=9001, recurso_ide=4321, obra_ide=694, obra_cod="0694",
            parte_ide=777, parte_cod="PT26/00319", parte_est=1,
            en_registro=True, hora="MADM", can=0.95, fec=20260930,
            paride=2105, partida_cod="CI.1.5", partida_res="JEFE DE OBRA",
            synckey=None)]


@pytest.mark.parametrize("est, en_registro", [(1, True), (3, False),
                                              (10, False), (None, False)])
def test_f054_r6_en_registro_es_el_estado_activo(est, en_registro):
    cli, _ = _cliente_historial([dict(FILA, parte_est=est)])
    [ls] = cli.lineas_mensuales_del_periodo(1, 2026, 9)
    assert ls.parte_est == est
    assert ls.en_registro is en_registro


def test_f054_r6_en_registro_con_el_estado_del_ajuste():
    cli, _ = _cliente_historial([dict(FILA, parte_est=7)], est_parte=7)
    assert cli.lineas_mensuales_del_periodo(1, 2026, 9)[0].en_registro


def test_f054_r6_nulos_y_texto():
    vacia = dict(FILA, obra_cod=None, parte_cod="  ", hora=None, paride=None,
                 par_cod=None, par_res=None, synckey="   ")
    texto = dict(FILA, ide="9002", reside="12", obride="5", parte_ide="6",
                 can="0.5", fec="20260930", paride="7", parte_est="1",
                 synckey=" partes:3 ")
    cli, _ = _cliente_historial([vacia, texto])
    a, b = cli.lineas_mensuales_del_periodo(1, 2026, 9)
    assert (a.obra_cod, a.parte_cod, a.hora, a.paride, a.partida_cod,
            a.partida_res, a.synckey) == (None, None, None, 0, None, None,
                                          None)
    assert (b.hmores_ide, b.recurso_ide, b.obra_ide, b.parte_ide, b.can,
            b.fec, b.paride, b.parte_est, b.en_registro, b.synckey) == (
        9002, 12, 5, 6, 0.5, 20260930, 7, 1, True, "partes:3")


def test_f054_r4_una_lectura_medida_por_trozo_con_su_nombre():
    cli, _ = _cliente_historial([FILA])
    with medir_lecturas() as m:
        cli.lineas_mensuales_del_periodo(1, 2026, 9)
        cli.lineas_mensuales_del_periodo(
            1, 2026, 9, resides=range(1, LOTE_PARAMETROS + 2))
    assert [(l.nombre, l.filas) for l in m.lecturas] == [
        ("lineas_mensuales_del_periodo", 1)] * 3


def test_f054_r3_truncado_es_error(monkeypatch):
    from tests.test_f047_tope_filas import _cliente, _emulada
    _emulada(monkeypatch, [dict(FILA), dict(FILA)])
    with pytest.raises(RuntimeError, match="truncada"):
        _cliente(max_rows=1).lineas_mensuales_del_periodo(1, 2026, 9)


def test_f054_r3_ok_false_es_error(monkeypatch):
    from infrastructure.sigrid import sigrid_write_client as mod

    from tests.test_f047_tope_filas import _cliente, _Respuesta
    monkeypatch.setattr(mod.httpx, "post", lambda *a, **k: _Respuesta(
        {"ok": False, "error": "timeout"}))
    with pytest.raises(RuntimeError, match="ok=false"):
        _cliente().lineas_mensuales_del_periodo(1, 2026, 9)
