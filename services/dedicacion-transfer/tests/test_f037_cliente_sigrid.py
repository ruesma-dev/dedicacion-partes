# tests/test_f037_cliente_sigrid.py
"""F-037 · Cliente de Sigrid: lecturas nuevas, `caaide` y alta protegida.

Trazabilidad con `specs/F-037-asiento-analitico-obra/requirements.md`: R1
(`caaide` en el INSERT), R2-R4 y R7 (lecturas de horas, cuentas y
partidas), R9 y R16 (partes del periodo; `truncated` lanza), R11 y D17
(correlativo y `hmo` por empresa, alta condicional) y R17 (ninguna sentencia
toca asientos ni cambia estados). SQL de design §6.

Sin red: `_read` se sustituye por una lectura falsa que anota cada consulta,
y `httpx.post` por una respuesta fija cuando lo que se prueba es `_read`.
"""
from __future__ import annotations

import re

import pytest
from domain.models.registro_models import (
    HoraRecurso, ObraEntrada, ParteSigrid, PartidaCuenta,
)
from infrastructure.sigrid import sigrid_write_client as mod
from infrastructure.sigrid.sigrid_write_client import SigridWriteClient


class LecturaFalsa:
    """Sustituye a `_read`: anota (sql, params) y devuelve las filas
    fijadas (o una lista por llamada, en orden)."""

    def __init__(self, *respuestas: list[dict]) -> None:
        self.respuestas = list(respuestas) or [[]]
        self.llamadas: list[tuple[str, list]] = []

    def __call__(self, sql: str, params: list) -> list[dict]:
        self.llamadas.append((" ".join(sql.split()), list(params)))
        i = min(len(self.llamadas), len(self.respuestas)) - 1
        return list(self.respuestas[i])


def _cliente(*respuestas) -> tuple[SigridWriteClient, LecturaFalsa]:
    cli = SigridWriteClient(base_url="http://sigrid.invalid",
                            function_key="sin-clave", database="ruesma",
                            tip_parte=35, est_parte=1)
    lectura = LecturaFalsa(*respuestas)
    cli._read = lectura                       # type: ignore[method-assign]
    return cli, lectura


def _obra(empresa: int = 1) -> ObraEntrada:
    o = ObraEntrada(ide=828942, codigo="0404", nombre="PRUEBAS",
                    empresa=empresa)
    setattr(o, "cenide", 828943)
    return o


# ============================ R16 · _read ============================ #

class _Respuesta:
    def __init__(self, cuerpo: dict) -> None:
        self.status_code = 200
        self._cuerpo = cuerpo
        self.text = str(cuerpo)

    def json(self) -> dict:
        return self._cuerpo


def _read_con(monkeypatch, cuerpo: dict) -> list[dict]:
    monkeypatch.setattr(mod.httpx, "post",
                        lambda *a, **kw: _Respuesta(cuerpo))
    cli = SigridWriteClient(base_url="http://sigrid.invalid",
                            function_key="sin-clave", database="ruesma")
    return cli._read("SELECT 1 AS x", [])


def test_f037_r16_read_truncado_lanza(monkeypatch):
    with pytest.raises(RuntimeError, match="truncada"):
        _read_con(monkeypatch, {"ok": True, "columns": ["X"],
                                "rows": [[1]], "truncated": True})


@pytest.mark.parametrize("extra", [{}, {"truncated": False}])
def test_f037_r16_read_completo_devuelve_filas(monkeypatch, extra):
    filas = _read_con(monkeypatch, {"ok": True, "columns": ["X"],
                                    "rows": [[1], [2]], **extra})
    assert filas == [{"x": 1}, {"x": 2}]


# ===================== R2 · horas con su plantilla ===================== #

def test_f037_r2_horas_traen_cuenta_de_plantilla_y_defecto():
    cli, lectura = _cliente([
        {"reside": 200, "horide": 5, "cod": " MENC ", "res": "Encargado",
         "pre": 9000, "caacod": " 00000.CIMO03 ", "defecto": 1},
        {"reside": 200, "horide": 9, "cod": "HEGR", "res": None,
         "pre": None, "caacod": None, "defecto": 0},
        {"reside": 400, "horide": 6, "cod": "MJEFO", "res": None,
         "pre": 11000, "caacod": "  ", "defecto": 0},
    ])
    horas = cli.horas_de_recursos([400, 200, 200, None, 0])
    assert horas == {
        200: [HoraRecurso(5, "MENC", "Encargado", 9000.0,
                          caa_cod="00000.CIMO03", defecto=True),
              HoraRecurso(9, "HEGR", None, 0.0, caa_cod=None,
                          defecto=False)],
        400: [HoraRecurso(6, "MJEFO", None, 11000.0, caa_cod=None,
                          defecto=False)]}
    [(sql, params)] = lectura.llamadas
    assert params == [200, 400]
    for trozo in ("cc.cod AS caacod",
                  "CASE WHEN reshor.horide = res.horide THEN 1 ELSE 0 END "
                  "AS defecto",
                  "LEFT JOIN res ON res.ide = reshor.reside",
                  "LEFT JOIN con cc ON cc.ide = reshor.caaide AND "
                  "ISNULL(reshor.caaide, 0) <> 0",
                  "WHERE reshor.reside IN (?,?)"):
        assert trozo in sql, trozo
    assert "conide" not in sql                  # F-026 R19


def test_f037_r2_horas_sin_recursos_no_lee():
    cli, lectura = _cliente()
    assert cli.horas_de_recursos([None, 0]) == {}
    assert lectura.llamadas == []


# ===================== R4 · cuentas del centro ===================== #

def test_f037_r4_cuentas_del_centro_una_lectura_parametrizada():
    cli, lectura = _cliente([
        {"caaide": 701, "cod": "0404.CIMO03"},
        {"caaide": 702, "cod": "0404.CIMO02"},
        {"caaide": 703, "cod": "0404. CIMO02"},
    ])
    cuentas = cli.cuentas_de_centro(828943, 1, ["CIMO03", None, "CIMO02",
                                                "CIMO03"])
    assert cuentas == {"CIMO03": [(701, "0404.CIMO03")],
                       "CIMO02": [(702, "0404.CIMO02"),
                                  (703, "0404. CIMO02")]}
    [(sql, params)] = lectura.llamadas
    assert params == [828943, 1, "CIMO02", "CIMO03"]
    assert "FROM caa a JOIN con c ON c.ide = a.ide" in sql
    assert "WHERE a.cenide = ? AND c.emp = ?" in sql
    assert "IN (?,?)" in sql and "CIMO" not in sql


def test_f037_r4_cuentas_sin_subcuentas_no_lee():
    cli, lectura = _cliente()
    assert cli.cuentas_de_centro(828943, 1, [None]) == {}
    assert lectura.llamadas == []


# ===================== R9 · partes del periodo ===================== #

def test_f037_r9_partes_del_periodo_con_su_estado_en_una_lectura():
    cli, lectura = _cliente([
        {"ide": 12, "cod": "PT26/00012", "est": 10},
        {"ide": 7, "cod": "PT26/00007", "est": 1},
        {"ide": 5, "cod": "PT26/00005", "est": None},
    ])
    partes = cli.partes_del_periodo(828942, 2026, 7)
    assert partes == [ParteSigrid(12, "PT26/00012", 10),
                      ParteSigrid(7, "PT26/00007", 1),
                      ParteSigrid(5, "PT26/00005", None)]
    [(sql, params)] = lectura.llamadas
    assert sql == (
        "SELECT hmo.ide AS ide, con.cod AS cod, con.est AS est FROM hmo "
        "JOIN con ON con.ide = hmo.ide WHERE hmo.obride = ? AND "
        "hmo.ano = ? AND hmo.mes = ? AND ISNULL(hmo.reside, 0) = 0 AND "
        "con.tip = ? ORDER BY hmo.ide DESC")
    assert params == [828942, 2026, 7, 35]


def test_f037_r9_partes_del_periodo_vacio():
    cli, _ = _cliente([])
    assert cli.partes_del_periodo(1, 2026, 7) == []


# ===================== R3 · partidas de las líneas ===================== #

def test_f037_r3_partidas_con_su_cuenta_en_una_lectura():
    cli, lectura = _cliente([
        {"ide": 80001, "cod": " CI.1.10 ", "caacod": " 0678.CIMO03 "},
        {"ide": 80002, "cod": "CI.1.20", "caacod": None},
        {"ide": 80003, "cod": None, "caacod": "  "},
    ])
    partidas = cli.partidas_de_lineas([80002, None, 80001, 80003, 80001, 0])
    assert partidas == {
        80001: PartidaCuenta(80001, "CI.1.10", "0678.CIMO03"),
        80002: PartidaCuenta(80002, "CI.1.20", None),
        80003: PartidaCuenta(80003, None, None)}
    [(sql, params)] = lectura.llamadas
    assert params == [80001, 80002, 80003]
    assert sql == (
        "SELECT p.ide AS ide, p.cod AS cod, pc.cod AS caacod FROM obrparpar "
        "p LEFT JOIN con pc ON pc.ide = p.caaide AND ISNULL(p.caaide, 0) "
        "<> 0 WHERE p.ide IN (?,?,?)")


def test_f037_r3_partidas_sin_ides_no_lee():
    cli, lectura = _cliente()
    assert cli.partidas_de_lineas([None, 0]) == {}
    assert lectura.llamadas == []


# ===================== R1 · caaide en la línea ===================== #

def _insert(cli, **kw):
    datos = dict(hmoide=777, obra=_obra(), reside=200, pos=128,
                 fecha_int=20260731, horide=5, can=0.4, pre=9000.0,
                 ano=2026, mes=7, synckey="porcentajes:1", tex=None,
                 paride=80001)
    datos.update(kw)
    return cli.stmt_insert_linea(**datos)


def test_f037_r1_insert_lleva_caaide_en_su_posicion():
    cli, _ = _cliente()
    st = _insert(cli, caaide=90001)
    sql = " ".join(st["sql"].split())
    columnas = sql[sql.index("(") + 1:sql.index(")")].split(", ")
    valores = sql[sql.index("SELECT ") + 7:sql.index(" FROM")].split(", ")
    assert len(columnas) == len(valores)
    # `ide` es el MAX+1; el resto, por orden, `?` o un literal fijo.
    params = iter(st["parameters"])
    fila = {c: (next(params) if v == "?" else v)
            for c, v in zip(columnas[1:], valores[1:])}
    assert next(params, "fin") == "fin"
    assert fila["caaide"] == 90001
    assert (fila["cenide"], fila["obride"], fila["paride"]) == (
        828943, 828942, 80001)
    assert (fila["fac"], fila["ortide"]) == ("0", "0")
    assert (fila["tex"], fila["synckey"]) == ("", "porcentajes:1")


def test_f037_r1_insert_sin_cuenta_escribe_cero():
    cli, _ = _cliente()
    assert _insert(cli)["parameters"] == _insert(cli, caaide=0)["parameters"]
    assert _insert(cli, caaide=None)["parameters"][-3] == 0


def test_f037_r1_insert_sin_partida_escribe_cero():
    """T10: la firma conserva `paride = 0` por defecto."""
    cli, _ = _cliente()
    datos = dict(hmoide=777, obra=_obra(), reside=200, pos=128,
                 fecha_int=20260731, horide=5, can=0.4, pre=9000.0,
                 ano=2026, mes=7, synckey="porcentajes:1", tex=None)
    assert cli.stmt_insert_linea(**datos)["parameters"][4] == 0


# ======================= R17 · lo que NO se hace ======================= #

def test_f037_r17_ninguna_sentencia_toca_asientos_ni_estados():
    cli, _ = _cliente()
    sentencias = (cli.stmts_crear_parte(obra=_obra(), ano=2026, mes=7,
                                        cod="PT26/00350", desc="Parte X")
                  + [_insert(cli, caaide=1), cli.stmt_borrar_linea(5)])
    for st in sentencias:
        sql = " ".join(st["sql"].split()).lower()
        assert re.search(r"\b(asi|asa|apu|apa)\b", sql) is None, sql
        assert not sql.startswith("update"), sql
        assert "update con" not in sql and "delete from con" not in sql
        assert "delete from hmo " not in sql


# ============ R11 · correlativo por empresa (bug de antes de F-037) ============ #

@pytest.mark.parametrize("maxcod, esperado", [
    ("PT26/00349", "PT26/00350"), (None, "PT26/00001"),
    ("PT26/raro", "PT26/00001"), ("PT26", "PT26/00001"),
])
def test_f037_r11_siguiente_cod_pt_es_por_empresa(maxcod, esperado):
    cli, lectura = _cliente([{"maxcod": maxcod}])
    assert cli.siguiente_cod_pt(2026, 28) == esperado
    [(sql, params)] = lectura.llamadas
    assert sql == ("SELECT MAX(cod) AS maxcod FROM con WHERE cod LIKE ? "
                   "AND emp = ?")
    assert params == ["PT26/%", 28]


def test_f037_r11_siguiente_cod_pt_sin_filas_y_empresa_obligatoria():
    import inspect

    cli, _ = _cliente([])
    assert cli.siguiente_cod_pt(2027, 1) == "PT27/00001"
    empresa = inspect.signature(SigridWriteClient.siguiente_cod_pt
                                ).parameters["empresa"]
    assert empresa.default is inspect.Parameter.empty


# ================= R11 y D17 · alta protegida del parte ================= #

def _alta(empresa: int = 1, cod: str = "PT26/00350") -> list[dict]:
    cli, _ = _cliente()
    return cli.stmts_crear_parte(obra=_obra(empresa), ano=2026, mes=7,
                                 cod=cod, desc="Parte PRUEBAS")


def test_f037_r11_la_descripcion_del_parte_se_corta_a_128():
    """T10: `con.res` admite 128 caracteres; el alta no los excede."""
    cli, _ = _cliente()
    [con, _hmo] = cli.stmts_crear_parte(obra=_obra(), ano=2026, mes=7,
                                        cod="PT26/00350", desc="P" * 200)
    assert con["parameters"][4] == "P" * 128


def test_f037_r11_d17_forma_del_alta_y_sus_parametros():
    con, hmo = _alta(empresa=28)
    sql = " ".join(con["sql"].split())
    assert sql.count("?") == len(con["parameters"])
    # Los seis primeros, en el orden de antes (test_f022_r17).
    assert con["parameters"][:6] == [28, 35, 1, "PT26/00350",
                                     "Parte PRUEBAS", 20260731]
    # Código libre en la empresa y ningún parte En registro del periodo.
    assert con["parameters"][6:] == ["PT26/00350", 28, 35,
                                     828942, 2026, 7, 35, 1]
    # La condición va FUERA del agregado (design §6.5, la trampa).
    assert "AS n FROM con WITH (UPDLOCK, HOLDLOCK)) x WHERE NOT EXISTS" in sql
    assert sql.count("NOT EXISTS") == 2
    assert sql.count("WITH (UPDLOCK, HOLDLOCK)") == 4
    sql_hmo = " ".join(hmo["sql"].split())
    assert sql_hmo.count("?") == len(hmo["parameters"])
    assert "WHERE cod = ? AND tip = ? AND emp = ?" in sql_hmo
    assert "NOT EXISTS (SELECT 1 FROM hmo h WHERE h.ide = con.ide)" in sql_hmo
    assert hmo["parameters"] == [828943, 828942, 2026, 7, "PT26/00350", 35,
                                 28]


def _sqlite(*partes: tuple) -> "sqlite3.Connection":  # noqa: F821
    """Emulación EN MEMORIA de `con` y `hmo` para ejecutar el alta tal cual
    (sin las pistas de bloqueo de SQL Server). No es Sigrid ni ninguna BBDD
    del sistema: es un fixture. `partes`: (ide, emp, est, cod, obride)."""
    import sqlite3

    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE con (ide INTEGER, emp INTEGER, tip INTEGER, "
               "est INTEGER, cod TEXT, res TEXT, fec INTEGER)")
    db.execute("CREATE TABLE hmo (ide INTEGER, cenide INTEGER, "
               "obride INTEGER, ano INTEGER, mes INTEGER, reside INTEGER, "
               "cenmul INTEGER)")
    for ide, emp, est, cod, obride in partes:
        db.execute("INSERT INTO con VALUES (?, ?, 35, ?, ?, 'x', 20260731)",
                   [ide, emp, est, cod])
        db.execute("INSERT INTO hmo VALUES (?, 1, ?, 2026, 7, NULL, 0)",
                   [ide, obride])
    db.execute("INSERT INTO con VALUES (900, 1, 20, 1, 'XRT', 'otro', 0)")
    return db


def _ejecutar(db, sentencias: list[dict]) -> None:
    for st in sentencias:
        sql = (st["sql"].replace(" WITH (UPDLOCK, HOLDLOCK)", "")
               .replace("ISNULL(", "IFNULL("))
        db.execute(sql, st["parameters"])


def _partes(db) -> list[tuple]:
    return db.execute(
        "SELECT con.ide, con.emp, con.est, con.cod, hmo.obride FROM con "
        "JOIN hmo ON hmo.ide = con.ide ORDER BY con.ide").fetchall()


def test_f037_d17_alta_libre_crea_con_y_hmo():
    db = _sqlite()
    _ejecutar(db, _alta())
    assert _partes(db) == [(901, 1, 1, "PT26/00350", 828942)]
    _ejecutar(db, _alta()[1:])              # el hmo no se duplica
    assert db.execute("SELECT COUNT(*) FROM hmo").fetchone() == (1,)


def test_f037_d17_con_un_parte_en_registro_del_periodo_no_crea_nada():
    db = _sqlite((500, 1, 1, "PT26/00300", 828942))
    _ejecutar(db, _alta())
    assert _partes(db) == [(500, 1, 1, "PT26/00300", 828942)]
    assert db.execute("SELECT COUNT(*) FROM con").fetchone() == (2,)


def test_f037_d17_con_solo_cerrados_crea_el_complementario():
    db = _sqlite((500, 1, 10, "PT26/00300", 828942),
                 (501, 1, 1, "PT26/00301", 111))       # En registro, OTRA obra
    _ejecutar(db, _alta())
    assert _partes(db)[-1] == (901, 1, 1, "PT26/00350", 828942)


def test_f037_d17_codigo_ocupado_en_la_empresa_no_crea_nada():
    db = _sqlite((500, 1, 10, "PT26/00350", 111))
    _ejecutar(db, _alta())
    assert _partes(db) == [(500, 1, 10, "PT26/00350", 111)]


def test_f037_r11_codigo_ocupado_en_otra_empresa_si_crea_y_hmo_por_emp():
    """El correlativo es por empresa: el mismo código en la 28 no impide el
    alta en la 1, y el `hmo` solo se cuelga del `con` de SU empresa."""
    db = _sqlite((500, 28, 1, "PT26/00350", 111))
    db.execute("DELETE FROM hmo WHERE ide = 500")    # con sin hmo en la 28
    _ejecutar(db, _alta(empresa=1))
    assert _partes(db) == [(901, 1, 1, "PT26/00350", 828942)]
    assert db.execute("SELECT COUNT(*) FROM hmo").fetchone() == (1,)
