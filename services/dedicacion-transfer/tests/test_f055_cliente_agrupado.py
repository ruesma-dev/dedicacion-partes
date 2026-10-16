# tests/test_f055_cliente_agrupado.py
"""F-055 · T5: lecturas agrupadas del cliente de Sigrid (R20).

`obras_por_ide`, `partes_de_periodos` y `lineas_de_partes` son el SQL de su
lectura suelta (`obra_por_ide`, `partes_del_periodo`, `lineas_del_parte`)
con `IN (?…)` y la clave en la salida; cada clave sale con lo MISMO que la
suelta y en el mismo orden. `horas_de_recursos` pasa a trozos de 500. Un
`truncated` es error. El `ClienteFalso` de `conftest.py` los deriva de sus
lecturas sueltas.

Sin red ni BBDD: `_read` sustituido por un doble. Los `ide` son inventados.
"""
from __future__ import annotations

import pytest
from domain.models.registro_models import ParteSigrid

from tests.conftest import ClienteFalso
from tests.test_f050_propuesta import _cliente_historial


def _sql(falso, i=0) -> str:
    return falso.llamadas[i][0]


def _suelta(metodo, filas, *args):
    """Lo que devuelve la lectura suelta con esas `filas`."""
    cli, _ = _cliente_historial(filas)
    return getattr(cli, metodo)(*args)


# =============================== obras ================================== #
FILA_OBRA = {"ide": 7, "cod": "0694", "res": "OBRA 7", "cenide": 70,
             "emp": 1}


def test_f055_r20_obras_por_ide_mismo_sql_con_in():
    cli, falso = _cliente_historial()
    cli.obra_por_ide(7)
    suelta = _sql(falso)
    cli, falso = _cliente_historial()
    cli.obras_por_ide([9, 7, 9, None, 0])
    assert _sql(falso) == suelta.replace("WHERE obr.ide = ?",
                                         "WHERE obr.ide IN (?,?)")
    assert falso.llamadas[0][1] == [7, 9]


def test_f055_r20_obras_por_ide_por_clave_como_la_suelta():
    otra = dict(FILA_OBRA, ide=9, cod="0696", cenide=None, emp=None)
    cli, _ = _cliente_historial([otra, FILA_OBRA])
    obras = cli.obras_por_ide([7, 9, 11])
    assert sorted(obras) == [7, 9]                    # la 11 no existe
    for ide, fila in ((7, FILA_OBRA), (9, otra)):
        esperada = _suelta("obra_por_ide", [fila], ide)
        assert obras[ide] == esperada
        assert obras[ide].cenide == esperada.cenide


def test_f055_r20_obras_por_ide_sin_ides_no_lee():
    cli, falso = _cliente_historial()
    assert cli.obras_por_ide([None, 0]) == {}
    assert falso.llamadas == []


# =============================== partes ================================= #
def _parte(ide, obride, ano, mes, est=1):
    return {"ide": ide, "cod": f"PT{ide}", "est": est, "obride": obride,
            "ano": ano, "mes": mes}


def test_f055_r20_partes_de_periodos_mismo_sql_con_in():
    cli, falso = _cliente_historial(tip_parte=35)
    cli.partes_del_periodo(5, 2026, 9)
    suelta = " ".join(_sql(falso).split())
    cli, falso = _cliente_historial(tip_parte=35)
    cli.partes_de_periodos([6, 5, 6], [(2026, 9), (2026, 8), (2026, 9)])
    sql, params = falso.llamadas[0]
    assert sql.startswith("SELECT hmo.ide AS ide, con.cod AS cod, "
                          "con.est AS est, hmo.obride AS obride, "
                          "hmo.ano AS ano, hmo.mes AS mes FROM hmo ")
    assert ("WHERE hmo.obride IN (?,?) AND (hmo.ano * 100 + hmo.mes) "
            "IN (?,?) AND ISNULL(hmo.reside, 0) = 0 AND con.tip = ? "
            "ORDER BY hmo.ide DESC") in sql
    assert "JOIN con ON con.ide = hmo.ide" in sql and \
        "JOIN con ON con.ide = hmo.ide" in suelta
    assert params == [5, 6, 202608, 202609, 35]


def test_f055_r20_partes_de_periodos_por_clave_y_orden_como_la_suelta():
    filas = [_parte(30, 5, 2026, 9), _parte(29, 6, 2026, 9),
             _parte(28, 5, 2026, 9, est=3), _parte(27, 5, 2026, 8),
             _parte(26, 6, 2026, 7)]                # periodo no pedido
    cli, _ = _cliente_historial(filas)
    partes = cli.partes_de_periodos([5, 6], [(2026, 9), (2026, 8)])
    assert sorted(partes) == [(5, 2026, 8), (5, 2026, 9), (6, 2026, 8),
                              (6, 2026, 9)]
    assert partes[(5, 2026, 9)] == [ParteSigrid(30, "PT30", 1),
                                    ParteSigrid(28, "PT28", 3)]
    assert partes[(6, 2026, 8)] == []
    suelta = _suelta("partes_del_periodo",
                     [f for f in filas if (f["obride"], f["mes"]) == (5, 9)],
                     5, 2026, 9)
    assert partes[(5, 2026, 9)] == suelta


def test_f055_r20_partes_sin_obras_o_periodos_no_lee():
    cli, falso = _cliente_historial()
    assert cli.partes_de_periodos([], [(2026, 9)]) == {}
    assert cli.partes_de_periodos([5], []) == {}
    assert falso.llamadas == []


def test_f055_r20_partes_en_trozos_de_500_obras():
    cli, falso = _cliente_historial()
    cli.partes_de_periodos(range(1, 1002), [(2026, 9)])
    assert [len(p) - 2 for _, p in falso.llamadas] == [500, 500, 1]


# ================================ líneas ================================= #
def _ls(ide, hmoide, reside, pos):
    return {"ide": ide, "hmoide": hmoide, "reside": reside, "fec": 20260930,
            "horide": 5, "paride": 80001, "hora": "MENC", "can": 0.5,
            "tot": 10.0, "synckey": "porcentajes:1 " if ide == 3 else None,
            "pos": pos}


def test_f055_r20_lineas_de_partes_mismo_sql_con_in():
    cli, falso = _cliente_historial()
    cli.lineas_del_parte(1, [200])
    suelta = _sql(falso)
    cli, falso = _cliente_historial()
    cli.lineas_de_partes([2, 1], [400, 200, 400])
    sql, params = falso.llamadas[0]
    assert sql == suelta.replace(
        "SELECT hmores.ide AS ide,",
        "SELECT hmores.hmoide AS hmoide, hmores.pos AS pos, "
        "hmores.ide AS ide,").replace(
        "WHERE hmores.hmoide = ? AND hmores.reside IN (?)",
        "WHERE hmores.hmoide IN (?,?) AND hmores.reside IN (?,?)").replace(
        "ORDER BY hmores.pos", "ORDER BY hmores.hmoide, hmores.pos")
    assert params == [1, 2, 200, 400]


def test_f055_r20_lineas_de_partes_por_clave_y_orden_como_la_suelta():
    filas = [_ls(1, 10, 200, 64), _ls(2, 11, 200, 64), _ls(3, 10, 400, 128)]
    cli, _ = _cliente_historial(filas)
    lineas = cli.lineas_de_partes([10, 11, 12], [200, 400])
    assert sorted(lineas) == [10, 11, 12]
    assert lineas[12] == []
    for hmoide in (10, 11):
        assert lineas[hmoide] == _suelta(
            "lineas_del_parte", [f for f in filas if f["hmoide"] == hmoide],
            hmoide, [200, 400])
    assert [l.ide for l in lineas[10]] == [1, 3]
    assert lineas[10][1].nuestra is True


def test_f055_r20_lineas_sin_partes_o_recursos_no_lee():
    cli, falso = _cliente_historial()
    assert cli.lineas_de_partes([], [200]) == {}
    assert cli.lineas_de_partes([1], [None]) == {}
    assert falso.llamadas == []


def test_f055_r20_lineas_en_trozos_de_500_por_lado():
    cli, falso = _cliente_historial()
    cli.lineas_de_partes(range(1, 502), range(1, 503))
    assert [len(p) for _, p in falso.llamadas] == [1000, 502, 501, 3]


# ================================ horas ================================== #
def test_f055_r20_horas_de_recursos_en_trozos_de_500():
    fila = {"reside": 1, "horide": 5, "cod": "MENC ", "res": "M", "pre": 9.0,
            "caacod": None, "defecto": 1}
    cli, falso = _cliente_historial([fila])
    horas = cli.horas_de_recursos(range(1, 1102))
    assert [len(p) for _, p in falso.llamadas] == [500, 500, 101]
    assert falso.llamadas[1][1][0] == 501
    assert [h.cod for h in horas[1]] == ["MENC"] * 3      # una por trozo


# =============================== truncado ================================ #
@pytest.mark.parametrize("metodo, args, fila", [
    ("obras_por_ide", ([7, 9],), FILA_OBRA),
    ("partes_de_periodos", ([5], [(2026, 9)]), _parte(1, 5, 2026, 9)),
    ("lineas_de_partes", ([10], [200]), _ls(1, 10, 200, 64)),
])
def test_f055_r20_truncado_es_error(monkeypatch, metodo, args, fila):
    from tests.test_f047_tope_filas import _cliente as cliente_emulado
    from tests.test_f047_tope_filas import _emulada
    _emulada(monkeypatch, [dict(fila), dict(fila, ide=99)])
    with pytest.raises(RuntimeError, match="truncada"):
        getattr(cliente_emulado(max_rows=1), metodo)(*args)


def test_f055_r20_cada_agrupada_se_mide_con_su_nombre():
    from infrastructure.sigrid.sigrid_write_client import medir_lecturas
    cli, _ = _cliente_historial()
    with medir_lecturas() as m:
        cli.obras_por_ide([1])
        cli.partes_de_periodos([1], [(2026, 9)])
        cli.lineas_de_partes([1], [1])
    assert [l.nombre for l in m.lecturas] == [
        "obras_por_ide", "partes_de_periodos", "lineas_de_partes"]


# ========================= el doble de conftest ========================== #
def test_f055_r20_el_doble_deriva_de_sus_lecturas_sueltas():
    cli = ClienteFalso()
    assert cli.obras_por_ide([5, 6]) == {5: cli.obra_por_ide(5),
                                         6: cli.obra_por_ide(6)}
    assert cli.partes_de_periodos([1, 2], [(2026, 7), (2026, 8)]) == {
        (o, a, m): cli.partes_del_periodo(o, a, m)
        for o in (1, 2) for a, m in ((2026, 7), (2026, 8))}
    assert cli.lineas_de_partes([777], [200]) == {
        777: cli.lineas_del_parte(777, [200])}
    assert cli.obras_por_ide([]) == {}


# ========== T16 · huecos que dejó la campaña de mutación (cliente) ======== #
def test_f055_r20_linea_del_parte_mapea_nulos_y_valores():
    """Supervivientes de `_linea_del_parte` (`or 1`, `and 0`, `and None`):
    la fila de Sigrid con nulos sale con ceros y `horide` None; con valores,
    tal cual."""
    from domain.models.registro_models import LineaSigrid
    from infrastructure.sigrid.sigrid_write_client import SigridWriteClient
    vacia = {"ide": 1, "reside": None, "fec": None, "horide": None,
             "paride": None, "hora": None, "can": None, "tot": None,
             "synckey": None}
    llena = {"ide": 2, "reside": 200, "fec": 20260930, "horide": 5,
             "paride": 80001, "hora": "MENC", "can": 0.5, "tot": 10.0,
             "synckey": " porcentajes:7 "}
    assert SigridWriteClient._linea_del_parte(vacia) == LineaSigrid(
        ide=1, reside=0, fecha_int=0, horide=None, hora_codigo=None,
        can=None, tot=None, synckey=None, nuestra=False, paride=0)
    assert SigridWriteClient._linea_del_parte(llena) == LineaSigrid(
        ide=2, reside=200, fecha_int=20260930, horide=5, hora_codigo="MENC",
        can=0.5, tot=10.0, synckey="porcentajes:7", nuestra=True,
        paride=80001)


def test_f055_r1_la_lectura_medida_es_inmutable():
    """Superviviente `@dataclass(frozen=False)` en `Lectura`."""
    from dataclasses import FrozenInstanceError

    from infrastructure.sigrid.sigrid_write_client import Lectura
    with pytest.raises(FrozenInstanceError):
        Lectura("x", 1, 0.5).filas = 2


# ================= T17b · O3 de la review: orden por `pos` ================= #
def test_f055_r20_lineas_de_partes_en_varios_trozos_en_orden_pos():
    """Con más de 500 recursos la lectura va en varios trozos de recursos;
    cada parte sale en su orden `pos` global, como la suelta (el pipeline
    usa ese orden), no trozo a trozo."""
    trozo1 = [dict(_ls(1, 10, 1, 128), pos=128),
              dict(_ls(3, 10, 2, 320), pos=320)]
    trozo2 = [dict(_ls(2, 10, 600, 64), pos=64),
              dict(_ls(4, 10, 601, 256), pos=256)]
    respuestas = iter([trozo1, trozo2])
    cli, falso = _cliente_historial()
    cli._read = lambda sql, params: falso(sql, params) and [] or \
        next(respuestas)
    lineas = cli.lineas_de_partes([10], range(1, 602))
    assert len(falso.llamadas) == 2
    assert [l.ide for l in lineas[10]] == [2, 1, 4, 3]
    assert "hmores.pos AS pos" in falso.llamadas[0][0]
