# tests/test_f062_cliente_ventana.py
"""F-062 · La lectura de las rachas (R19, design §6) y el `UPDATE` de la
`fec` con el `can` leído (R14, D12), en el cliente de Sigrid.

Sin red: el cliente con su `_read` sustituido por un doble. Los `ide` son
inventados y no coinciden con ningún dato real.
"""
from __future__ import annotations

import pytest
from application.services.rachas import ventana
from domain.models.registro_models import LineaIncidenciaSigrid

from tests.test_f050_propuesta import _cliente_historial

FILA = {"ide": 9001, "reside": 200, "fec": 20261005, "cod": "CIV ",
        "synckey": " porcentajes:inc:7:ini ", "parte": " PT26/1 ", "can": 0,
        "hmoide": 777, "est": 1, "emp": 1, "obride": 40, "cenide": 7,
        "paride": 300, "caaide": 400}
SELECT = ("SELECT h.ide AS ide, h.reside AS reside, h.fec AS fec, "
          "a.cod AS cod, h.synckey AS synckey, c.cod AS parte, "
          "h.can AS can, h.hmoide AS hmoide, c.est AS est, c.emp AS emp, "
          "m.obride AS obride, h.cenide AS cenide, h.paride AS paride, "
          "h.caaide AS caaide FROM hmores h "
          "JOIN auxhor a ON a.ide = h.horide JOIN hmo m ON m.ide = h.hmoide "
          "JOIN con c ON c.ide = m.ide ")
ORDEN = " ORDER BY h.fec, h.ide"


def test_f062_r19_ventana_de_m_menos_n_a_m_mas_1():
    assert ventana(2026, 10, 12) == (20251001, 20261130)
    assert ventana(2026, 1, 1) == (20251201, 20260228)
    assert ventana(2026, 12, 12) == (20251201, 20270131)
    assert ventana(2028, 1, 13) == (20261201, 20280229)


def test_f062_r19_sql_por_recurso_o_por_ide_con_obra_centro_y_cuenta():
    cli, falso = _cliente_historial([
        dict(FILA, fec=20261009, ide=9003), FILA,
        dict(FILA, ide=9002, can=None, hmoide=None, est=None, emp=None,
             obride=None, cenide=None, paride=None, caaide=None, cod="CIZ")])
    filas = cli.incidencias_en_ventana([300, 200, None, 300], 20251001,
                                       20261130, ides=[9002, None, 9001])
    [(sql, params)] = falso.llamadas
    assert sql == SELECT + (
        "WHERE (h.reside IN (?,?) AND h.fec BETWEEN ? AND ? "
        "AND a.cod LIKE ? OR h.ide IN (?,?))" + ORDEN)
    assert params == [200, 300, 20251001, 20261130, "CI%", 9001, 9002]
    assert filas == [
        LineaIncidenciaSigrid(9001, 200, 20261005, "CIV",
                              "porcentajes:inc:7:ini", "PT26/1", can=0.0,
                              hmoide=777, parte_est=1, obride=40, cenide=7,
                              paride=300, caaide=400, parte_emp=1),
        LineaIncidenciaSigrid(9002, 200, 20261005, "CIZ",
                              "porcentajes:inc:7:ini", "PT26/1", can=None,
                              hmoide=None, parte_est=None),
        LineaIncidenciaSigrid(9003, 200, 20261009, "CIV",
                              "porcentajes:inc:7:ini", "PT26/1", can=0.0,
                              hmoide=777, parte_est=1, obride=40, cenide=7,
                              paride=300, caaide=400, parte_emp=1)]
    assert isinstance(filas[0].can, float)


def test_f062_r19_sql_en_pruebas_solo_la_obra_de_pruebas():
    cli, falso = _cliente_historial()
    cli.incidencias_en_ventana([200], 20251001, 20261130, obride_pruebas=40,
                               ides=[9001])
    [(sql, params)] = falso.llamadas
    assert sql == SELECT + (
        "WHERE (h.reside IN (?) AND h.fec BETWEEN ? AND ? "
        "AND a.cod LIKE ? OR h.ide IN (?)) AND m.obride = ?" + ORDEN)
    assert params == [200, 20251001, 20261130, "CI%", 9001, 40]
    cli, falso = _cliente_historial()
    cli.incidencias_en_ventana([200], 20251001, 20261130, obride_pruebas=40)
    [(sql, params)] = falso.llamadas
    assert sql == SELECT + (
        "WHERE h.reside IN (?) AND h.fec BETWEEN ? AND ? "
        "AND a.cod LIKE ? AND m.obride = ?" + ORDEN)
    assert params == [200, 20251001, 20261130, "CI%", 40]


def test_f062_r19_sql_solo_ides_o_nada():
    cli, falso = _cliente_historial()
    cli.incidencias_en_ventana([None, 0], 20251001, 20261130, ides=[9001])
    [(sql, params)] = falso.llamadas
    assert sql == SELECT + "WHERE (h.ide IN (?))" + ORDEN
    assert params == [9001]
    cli, falso = _cliente_historial([FILA])
    assert cli.incidencias_en_ventana([], 20251001, 20261130) == []
    assert cli.incidencias_en_ventana([None], 20251001, 20261130,
                                      ides=[None, 0]) == []
    assert falso.llamadas == []


def test_f062_r19_en_trozos_de_500_y_cada_linea_una_vez():
    cli, falso = _cliente_historial([FILA])
    filas = cli.incidencias_en_ventana(range(1, 601), 20251001, 20261130,
                                       ides=[9001, 9002])
    assert [len(p) for _, p in falso.llamadas] == [503, 105]
    assert falso.llamadas[1][1][-2:] == [9001, 9002]
    assert "OR h.ide IN" not in falso.llamadas[0][0]
    assert [f.ide for f in filas] == [9001]
    cli, falso = _cliente_historial()
    cli.incidencias_en_ventana(range(1, 501), 20251001, 20261130)
    assert len(falso.llamadas) == 1


def test_f062_r19_truncado_es_error_y_se_mide_con_su_nombre(monkeypatch):
    from infrastructure.sigrid.sigrid_write_client import medir_lecturas

    from tests.test_f047_tope_filas import _cliente as cliente_emulado
    from tests.test_f047_tope_filas import _emulada

    _emulada(monkeypatch, [dict(FILA), dict(FILA, ide=99)])
    with pytest.raises(RuntimeError, match="truncada"):
        cliente_emulado(max_rows=1).incidencias_en_ventana(
            [200], 20251001, 20261130)
    cli, _ = _cliente_historial()
    with medir_lecturas() as m:
        cli.incidencias_en_ventana([1], 20251001, 20261130)
    assert [x.nombre for x in m.lecturas] == ["incidencias_en_ventana"]


def test_f062_r14_d12_update_de_la_fec_con_el_can_leido():
    from tests.test_f030_r30_editar import GUARDA_INC

    cli, _ = _cliente_historial()
    st = cli.stmt_editar_fecha_incidencia(
        ide=62, reside=200, hora_codigo="CIZ", synckey_leida=None,
        fecha_int=20261016, fec_leida=20261009, can_leido=1.0)
    assert " ".join(st["sql"].split()) == (
        "UPDATE hmores SET fec = ? " + GUARDA_INC + " AND fec = ?")
    assert st["parameters"] == [20261016, 62, 200, 1.0, "", "CIZ", 1,
                                20261009]
    # Sin `can_leido`, la de hoy: `can` 0.
    hoy = cli.stmt_editar_fecha_incidencia(
        ide=62, reside=200, hora_codigo="CIZ", synckey_leida="k",
        fecha_int=20261016, fec_leida=20261009)
    assert hoy["parameters"][3] == 0.0
    nulo = cli.stmt_editar_fecha_incidencia(
        ide=62, reside=200, hora_codigo="CIZ", synckey_leida="k",
        fecha_int=20261016, fec_leida=20261009, can_leido=None)
    assert nulo["parameters"][3] == 0.0 and nulo["sql"] == hoy["sql"]


@pytest.mark.parametrize("valor, vale", [
    (None, 12), ("1", 1), ("24", 24), ("0", False), ("-3", False)])
def test_f062_r19_ajuste_incidencias_meses_atras(monkeypatch, valor, vale):
    from config.settings import Settings
    from pydantic import ValidationError

    monkeypatch.setenv("SIGRID_API_BASE_URL", "http://sigrid.invalid")
    monkeypatch.setenv("SIGRID_API_FUNCTION_KEY", "sin-clave")
    monkeypatch.delenv("INCIDENCIAS_MESES_ATRAS", raising=False)
    if valor is not None:
        monkeypatch.setenv("INCIDENCIAS_MESES_ATRAS", valor)
    if vale is False:
        with pytest.raises(ValidationError):
            Settings(_env_file=None)
    else:
        assert Settings(_env_file=None).incidencias_meses_atras == vale


def test_f062_r19_el_doble_del_conftest_lee_la_ventana():
    from tests.conftest import ClienteFalso, SettingsFalso

    cli = ClienteFalso()
    cli.lineas_incidencia = [LineaIncidenciaSigrid(
        1, 200, 20261005, "CIV", None, "PT26/1"), LineaIncidenciaSigrid(
        2, 201, 20261005, "CIV", None, "PT26/1"), LineaIncidenciaSigrid(
        3, 202, 20240105, "CIV", None, "PT26/1")]
    assert [x.ide for x in cli.incidencias_en_ventana(
        [200, 202], 20251001, 20261130, ides=[2])] == [1, 2]
    assert cli.leidas_ventana == [([200, 202], 20251001, 20261130, None,
                                   [2])]
    assert SettingsFalso().incidencias_meses_atras == 12
