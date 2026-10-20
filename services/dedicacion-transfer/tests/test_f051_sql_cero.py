# tests/test_f051_sql_cero.py
"""F-051 · SQL del cliente de Sigrid (design §7) y respuesta de
`POST /api/registro/ejecutar`.

- R15: `lineas_registradas(claves, ides)`, la lectura de lo ya registrado
  por `synckey` **o** `hmores.ide`; sin `ides`, la de hoy.
- R8, R10, R11: `lineas_para_editar`, `stmt_editar_linea` y
  `stmt_poner_a_cero`, con su guarda.

Sin red: `_read` se sustituye por una lectura falsa que anota cada consulta
(el patrón de `test_f037_cliente_sigrid.py`).
"""
from __future__ import annotations

import pytest
from application.services.lecturas_lote import LecturasDelLote
from infrastructure.sigrid import sigrid_write_client as mod
from infrastructure.sigrid.sigrid_write_client import (
    SigridWriteClient, medir_lecturas, synckey_de,
)

from tests.conftest import (
    OBRA_ORIGEN, ClienteFalso, SettingsFalso, linea, linea_previa,
)
from domain.models.registro_models import LineaSigrid, ObraEntrada


class LecturaFalsa:
    """Sustituye a `_read`: anota (sql, params) y devuelve las filas de
    `respuestas`, una lista por llamada (la última se repite)."""

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


def _fila(ide, synckey=None, **kw) -> dict:
    datos = {"ide": ide, "hmoide": 777, "reside": 200, "fec": 20261031,
             "horide": 5, "hora": "MENC", "can": 0.4, "tot": 3600.0,
             "synckey": synckey, "paride": 80001}
    datos.update(kw)
    return datos


# ================================ R15 ================================== #
def test_f051_r15_sin_ides_es_la_consulta_de_hoy():
    hoy, l_hoy = _cliente([_fila(9, synckey_de(1))])
    nuevo, l_nuevo = _cliente([_fila(9, synckey_de(1))])
    claves = [synckey_de(2), synckey_de(1)]
    with medir_lecturas() as m:
        por_sk, por_ide = nuevo.lineas_registradas(claves, [])
    esperado = hoy.lineas_por_synckey(claves)
    assert l_nuevo.llamadas == l_hoy.llamadas
    assert por_sk == esperado and por_ide == {}
    assert [l.nombre for l in m.lecturas] == ["lineas_por_synckey"]


def test_f051_r15_sin_claves_ni_ides_no_lee():
    cli, lectura = _cliente()
    assert cli.lineas_registradas([], []) == ({}, {})
    assert lectura.llamadas == []


def test_f051_r15_por_synckey_o_ide_en_una_lectura_parametrizada():
    cli, lectura = _cliente([
        _fila(9, f" {synckey_de(1)} "),
        _fila(410931, "partes:x", reside=410, can=0, paride=0),
        _fila(410935, None)])
    with medir_lecturas() as m:
        por_sk, por_ide = cli.lineas_registradas(
            [synckey_de(1), synckey_de(1)], [410935, 410931, None, 0])
    [(sql, params)] = lectura.llamadas
    assert "WHERE hmores.synckey IN (?) OR hmores.ide IN (?,?)" in sql
    assert params == [synckey_de(1), 410931, 410935]
    assert "porcentajes:1" not in sql and "410931" not in sql
    for campo in ("hmores.ide AS ide", "hmores.hmoide AS hmoide",
                  "hmores.reside AS reside", "hmores.synckey AS synckey",
                  "hmores.can AS can", "hmores.paride AS paride",
                  "auxhor.cod AS hora"):
        assert campo in sql, campo
    assert [l.nombre for l in m.lecturas] == ["lineas_registradas"]
    assert list(por_sk) == [synckey_de(1)]
    assert por_sk[synckey_de(1)].ide == 9 and por_sk[synckey_de(1)].nuestra
    assert sorted(por_ide) == [410931, 410935]
    otra = por_ide[410931]
    assert (otra.reside, otra.synckey, otra.nuestra, otra.hmoide,
            otra.can, otra.paride) == (410, "partes:x", False, 777, 0, 0)
    assert por_ide[410935].synckey is None


def test_f051_r15_la_misma_fila_por_las_dos_vias():
    cli, _ = _cliente([_fila(9, synckey_de(1))])
    por_sk, por_ide = cli.lineas_registradas([synckey_de(1)], [9])
    assert por_sk[synckey_de(1)] is por_ide[9]


def test_f051_r15_en_trozos_de_lote_parametros(monkeypatch):
    monkeypatch.setattr(mod, "LOTE_PARAMETROS", 3)
    cli, lectura = _cliente([])
    cli.lineas_registradas([synckey_de(i) for i in (1, 2)], [7, 8, 9])
    assert [p for _, p in lectura.llamadas] == [
        [synckey_de(1), synckey_de(2), 7], [8, 9]]
    assert "synckey IN (?,?) OR hmores.ide IN (?)" in lectura.llamadas[0][0]
    assert lectura.llamadas[1][0].endswith("WHERE hmores.ide IN (?,?)")


def test_f051_r15_solo_ides():
    cli, lectura = _cliente([])
    cli.lineas_registradas([], [5])
    [(sql, params)] = lectura.llamadas
    assert sql.endswith("WHERE hmores.ide IN (?)") and params == [5]


# ======================= R15 · el lote (misma ronda) ======================= #
class ClienteQueAnotaRegistradas(ClienteFalso):
    def __init__(self, **kw) -> None:
        super().__init__(**kw)
        self.registradas: list[tuple] = []

    def lineas_registradas(self, claves, ides=()):
        self.registradas.append((list(claves), list(ides)))
        return super().lineas_registradas(claves, ides)


def _peticiones():
    obra = ObraEntrada(ide=555001, codigo=OBRA_ORIGEN)
    return [(obra, [linea(registro_id=1, hmores_ide=410931),
                    linea(registro_id=2)]),
            (obra, [linea(registro_id=3, hmores_ide=410600)])]


def test_f051_r15_lote_precarga_claves_e_ides_en_una_lectura():
    cli = ClienteQueAnotaRegistradas()
    cli.lineas_parte = [linea_previa(ide=410931)]
    m = LecturasDelLote(cli, 4)
    m.precargar(_peticiones(), SettingsFalso())
    assert cli.registradas == [(
        [synckey_de(1), synckey_de(2), synckey_de(3)], [410600, 410931])]
    cli.registradas.clear()
    por_sk, por_ide = m.lineas_registradas([synckey_de(1)], [410931])
    assert cli.registradas == [] and m.fallos_de_memoria == {}
    assert por_sk == {} and list(por_ide) == [410931]
    assert m.lineas_registradas([synckey_de(3)], []) == ({}, {})
    assert cli.registradas == []


@pytest.mark.parametrize("claves, ides", [
    ([synckey_de(9)], []), ([synckey_de(1)], [5]),
])
def test_f051_r15_lote_fuera_de_lo_precargado_lee(claves, ides):
    cli = ClienteQueAnotaRegistradas()
    m = LecturasDelLote(cli, 4)
    m.precargar(_peticiones(), SettingsFalso())
    cli.registradas.clear()
    m.lineas_registradas(claves, ides)
    assert cli.registradas == [(claves, ides)]
    assert m.fallos_de_memoria == {"lineas_registradas": 1}


def test_f051_r15_lote_sin_precarga_lee():
    cli = ClienteQueAnotaRegistradas()
    m = LecturasDelLote(cli, 4)
    m.lineas_registradas([synckey_de(1)], [])
    assert m.fallos_de_memoria == {"lineas_registradas": 1}


def test_f051_r15_lote_sigue_sirviendo_lineas_por_synckey():
    cli = ClienteQueAnotaRegistradas()
    cli.synckeys = {synckey_de(1): linea_previa(ide=9)}
    m = LecturasDelLote(cli, 4)
    m.precargar(_peticiones(), SettingsFalso())
    assert m.lineas_por_synckey([synckey_de(1)]) == {
        synckey_de(1): cli.synckeys[synckey_de(1)]}
    # Justo las precargadas (no un subconjunto propio): de memoria también.
    todas = [synckey_de(1), synckey_de(2), synckey_de(3)]
    assert m.lineas_por_synckey(todas) == {
        synckey_de(1): cli.synckeys[synckey_de(1)]}
    assert m.fallos_de_memoria == {}


# ============================ R8, R10, R11 ============================ #
GUARDA = (
    "WHERE ide = ? AND reside = ? AND ABS(ISNULL(can, 0) - ?) < 0.000001 "
    "AND LTRIM(RTRIM(ISNULL(synckey, ''))) = ? "
    "AND ISNULL(dvaproide, 0) = 0 AND ISNULL(dvfproide, 0) = 0 "
    "AND ISNULL(hdereside, 0) = 0 AND ISNULL(empdpreide, 0) = 0 "
    "AND ISNULL(empabside, 0) = 0 AND ISNULL(emprccide, 0) = 0 "
    "AND EXISTS (SELECT 1 FROM auxhor a WHERE a.ide = hmores.horide "
    "AND a.cod LIKE 'M%') "
    "AND EXISTS (SELECT 1 FROM con c WHERE c.ide = hmores.hmoide "
    "AND c.est = ?)")

EDICION = dict(ide=410600, reside=200, can_leido=0.0, synckey_leida=None,
               horide=5, can=0.33333, pre=9000.0, paride=80001,
               caaide=90001, fecha_int=20261031, synckey=synckey_de(7),
               tex=None)


def _plano(st: dict) -> str:
    return " ".join(st["sql"].split())


def test_f051_r8_editar_cada_campo_del_set_y_la_guarda():
    cli, _ = _cliente()
    st = cli.stmt_editar_linea(**EDICION)
    assert _plano(st) == (
        "UPDATE hmores SET can = ?, pre = ?, tot = ?, horide = ?, "
        "paride = ?, caaide = ?, fec = ?, synckey = ? " + GUARDA)
    assert st["parameters"] == [
        0.3333, 9000.0, 2999.97, 5, 80001, 90001, 20261031, synckey_de(7),
        410600, 200, 0.0, "", 1]


def test_f051_r8_redondeos_como_el_insert():
    cli, _ = _cliente()
    datos = dict(hmoide=777, obra=ObraEntrada(ide=1), reside=200, pos=64,
                 fecha_int=20261031, horide=5, can=0.33333, pre=1.234,
                 ano=2026, mes=10, synckey=synckey_de(7), tex=None)
    ins = cli.stmt_insert_linea(**datos)["parameters"]
    ed = cli.stmt_editar_linea(**EDICION | {"pre": 1.234})["parameters"]
    # 0,3333 × 1,234 = 0,41129…: con dos decimales 0,41 (con tres, 0,411).
    assert ed[:3] == [ins[8], ins[9], ins[10]] == [0.3333, 1.234, 0.41]


def test_f051_r8_sin_partida_ni_cuenta_van_a_cero():
    """Como el insert: una partida o una cuenta nula se escribe 0."""
    cli, _ = _cliente()
    ed = cli.stmt_editar_linea(**EDICION | {"paride": None, "caaide": None})
    assert ed["parameters"][4:6] == [0, 0]


def test_f051_r10_tex_solo_en_pruebas():
    cli, _ = _cliente()
    st = cli.stmt_editar_linea(**EDICION | {"tex": "PRUEBA-PORC"})
    assert _plano(st).startswith(
        "UPDATE hmores SET can = ?, pre = ?, tot = ?, horide = ?, "
        "paride = ?, caaide = ?, fec = ?, synckey = ?, tex = ? WHERE ")
    assert st["parameters"][7:10] == [synckey_de(7), "PRUEBA-PORC", 410600]


def test_f051_r11_guarda_con_lo_leido():
    cli, _ = _cliente()
    st = cli.stmt_editar_linea(**EDICION | {
        "can_leido": None, "synckey_leida": " partes:x ", "reside": 410})
    assert st["parameters"][-5:] == [410600, 410, 0.0, "partes:x", 1]


def test_f051_r11_la_guarda_usa_el_estado_en_registro_del_cliente():
    cli = SigridWriteClient(base_url="http://x", function_key="k",
                            database="ruesma", est_parte=7)
    assert cli.stmt_editar_linea(**EDICION)["parameters"][-1] == 7
    assert cli.stmt_poner_a_cero(ide=1, reside=2, can_leido=0.5,
                                 synckey_leida="")["parameters"][-1] == 7


def test_f051_r5_r11_poner_a_cero_solo_can_y_tot_con_la_misma_guarda():
    cli, _ = _cliente()
    st = cli.stmt_poner_a_cero(ide=5005, reside=200, can_leido=0.5,
                               synckey_leida="porcentajes:3")
    assert _plano(st) == "UPDATE hmores SET can = 0, tot = 0 " + GUARDA
    assert st["parameters"] == [5005, 200, 0.5, "porcentajes:3", 1]


def test_f051_r6_ninguna_sentencia_de_edicion_borra_ni_concatena():
    cli, _ = _cliente()
    for st in (cli.stmt_editar_linea(**EDICION | {"tex": "PRUEBA-PORC"}),
               cli.stmt_poner_a_cero(ide=5005, reside=200, can_leido=0.5,
                                     synckey_leida="porcentajes:3")):
        sql = _plano(st)
        assert "DELETE" not in sql.upper()
        for valor in ("410600", "5005", "porcentajes", "PRUEBA", "80001"):
            assert valor not in sql, valor


def test_f051_r12_lineas_para_editar_una_lectura_con_todo():
    cli, lectura = _cliente([
        {"ide": 410600, "hmoide": 777, "reside": 200, "horide": 5,
         "hora": "MENC", "paride": 80001, "can": 0, "pre": 8500.0,
         "tot": 0, "caaide": 90001, "fec": 20261031, "synckey": " ",
         "tex": "copia", "parte": "PT26/00370", "est": 1, "enlazada": 0},
        {"ide": 5005, "hmoide": 778, "reside": 200, "horide": None,
         "hora": None, "paride": None, "can": None, "pre": None,
         "tot": None, "caaide": None, "fec": None, "synckey": "partes:x",
         "tex": None, "parte": "PT26/00371", "est": None, "enlazada": 1}])
    with medir_lecturas() as m:
        out = cli.lineas_para_editar([5005, 410600, 5005, None])
    [(sql, params)] = lectura.llamadas
    assert params == [5005, 410600]
    assert "WHERE hmores.ide IN (?,?)" in sql
    for trozo in ("hmores.pre AS pre", "hmores.caaide AS caaide",
                  "CAST(hmores.tex AS NVARCHAR(400)) AS tex",
                  "con.cod AS parte", "con.est AS est",
                  "JOIN con ON con.ide = hmores.hmoide",
                  "ISNULL(hmores.dvaproide, 0) <> 0",
                  "ISNULL(hmores.emprccide, 0) <> 0"):
        assert trozo in sql, trozo
    assert [l.nombre for l in m.lecturas] == ["lineas_para_editar"]
    a, b = out[410600], out[5005]
    assert (a.hmoide, a.parte_cod, a.parte_est, a.pre, a.caaide, a.tex,
            a.enlazada, a.synckey, a.hora_codigo, a.paride, a.can) == (
        777, "PT26/00370", 1, 8500.0, 90001, "copia", False, None, "MENC",
        80001, 0)
    assert (b.parte_est, b.pre, b.caaide, b.enlazada, b.horide,
            b.synckey, b.nuestra) == (None, None, 0, True, None, "partes:x",
                                      False)


def test_f051_r12_lineas_para_editar_sin_ides_no_lee():
    cli, lectura = _cliente()
    assert cli.lineas_para_editar([]) == {} and lectura.llamadas == []


def test_f051_r12_lineas_para_editar_en_trozos(monkeypatch):
    monkeypatch.setattr(mod, "LOTE_PARAMETROS", 2)
    cli, lectura = _cliente([])
    cli.lineas_para_editar([1, 2, 3])
    assert [p for _, p in lectura.llamadas] == [[1, 2], [3]]


# ====================== R16, R19 · respuesta de la app ====================== #
@pytest.fixture
def app_con_resultado(monkeypatch):
    """`build_app` con ajustes falsos y `RegistroPipeline.ejecutar`
    sustituido: devuelve un resultado hecho a mano y anota las líneas."""
    from types import SimpleNamespace

    from application.pipelines.registro_pipeline import RegistroPipeline
    from domain.models.registro_models import ResultadoRegistro
    from fastapi.testclient import TestClient
    from interface_adapters.api.app import build_app

    ajustes = SimpleNamespace(
        sigrid_api_base_url="http://sigrid.invalid",
        sigrid_api_function_key="sin-clave", sigrid_api_database="ruesma",
        sigrid_api_timeout_s=1.0, sigrid_max_statements=15,
        sigrid_max_rows=200_000,
        tip_parte_trabajo=35, est_parte_activo=1, obra_pruebas_forzar=True,
        obra_pruebas_cod="0404", marca_pruebas="PRUEBA-PORC",
        postventa_registrar=True, postventa_obra_cod="POSTV2", paso_pos=64)
    vistas: list = []
    traza = {"registro_id": 1, "ide": 410600, "hmoide": 777,
             "parte_cod": "PT26/00370", "antes": {"can": 0.0},
             "despues": {"can": 0.4}}

    def ejecutar(self, *, obra, lineas, pisar_claves=None, usuario=None):
        vistas.extend(lineas)
        return ResultadoRegistro(
            ok=True, obra_destino=ObraEntrada(ide=1, codigo="0404"),
            forzada_pruebas=True,
            escritas=[{"registro_id": 1, "editada": True,
                       "hmores_ide": 410600}],
            ya_registradas=[2], ya_registradas_ide={2: 9002},
            editadas=[traza], a_cero=[dict(traza, ide=5005)])

    monkeypatch.setattr(RegistroPipeline, "ejecutar", ejecutar)
    return TestClient(build_app(ajustes)), vistas


def test_f051_r16_respuesta_de_ejecutar_con_lo_editado(app_con_resultado):
    cliente, vistas = app_con_resultado
    r = cliente.post("/api/registro/ejecutar", json={
        "obra": {"codigo": "0678"},
        "lineas": [{"registro_id": 1, "ano": 2026, "mes": 10,
                    "porcentaje": 0.4, "empresa": 1, "hmores_ide": 410600},
                   {"registro_id": 2, "ano": 2026, "mes": 10,
                    "porcentaje": 0.2, "empresa": 1}]})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["borradas"] == 0
    assert cuerpo["escritas"] == [{"registro_id": 1, "editada": True,
                                   "hmores_ide": 410600}]
    assert cuerpo["ya_registradas_ide"] == {"2": 9002}
    assert [e["ide"] for e in cuerpo["editadas"]] == [410600]
    assert [e["ide"] for e in cuerpo["a_cero"]] == [5005]
    assert cuerpo["editadas"][0]["antes"] == {"can": 0.0}
    # R14: el `hmores_ide` de la api llega a la línea del dominio.
    assert [l.hmores_ide for l in vistas] == [410600, None]


# ======================= R18 · el script de pruebas ======================= #
def test_f051_r18_el_script_ensena_lo_que_edita(monkeypatch, capsys):
    """`preflight` imprime la línea al 0 % que se editaría y, del pisado,
    qué edita y qué pone a 0; `ejecutar`, lo editado y lo puesto a 0 (con
    su antes y después), y las omitidas con su motivo. Con el doble: no
    hay red."""
    import prueba_escritura_porcentajes as script
    from application.pipelines.registro_pipeline import RegistroPipeline

    cli = ClienteFalso(lineas_parte=[
        linea_previa(ide=410600, can=0.0, tot=0.0, paride=80001),
        linea_previa(ide=5003, reside=400, horide=6, hora_codigo="MJEFO",
                     paride=80002, can=0.3),
        linea_previa(ide=5009, reside=400, horide=6, hora_codigo="MJEFO",
                     paride=80002, can=0.2)])
    monkeypatch.setattr(script, "_lineas", lambda ano, mes: [
        linea(registro_id=1),
        linea(registro_id=2, recurso_ide=400, paride=80002,
              partida_cod="CI.1.20")])
    st = SettingsFalso()
    pl = RegistroPipeline(cliente=cli, settings=st)
    pf = script.fase_preflight(pl, st, 2026, 7)
    salida = capsys.readouterr().out
    assert "linea_cero=410600" in salida
    assert "edita=5003 a_cero=[5009]" in salida
    script.fase_ejecutar(pl, st, 2026, 7, True,
                         [c.clave for c in pf.conflictos])
    salida = capsys.readouterr().out
    assert "editadas=2 a_cero=1 borradas=0" in salida
    assert "EDITADA ide=410600 parte=PT26/00251 registro=1" in salida
    assert "A CERO ide=5009" in salida
    assert "antes={'can': 0.0" in salida


# =================== campaña de mutación (T14) =================== #
def test_f051_r15_fila_sin_parte_queda_con_hmoide_cero():
    """`lineas_registradas` con un `hmoide` nulo: 0, no un parte inventado."""
    cli, _ = _cliente([_fila(410600, hmoide=None)])
    _, por_ide = cli.lineas_registradas([], [410600])
    assert por_ide[410600].hmoide == 0


def test_f051_r12_una_linea_leida_sin_enlaces_no_es_enlazada():
    """Las líneas que no vienen de `lineas_para_editar` (preflight,
    relectura) no saben de enlaces: por defecto no son enlazadas."""
    cli, _ = _cliente([_fila(410600)])
    _, por_ide = cli.lineas_registradas([], [410600])
    assert por_ide[410600].enlazada is False
    assert LineaSigrid(ide=1, reside=2, fecha_int=3, horide=4,
                       hora_codigo="MENC", can=0.0, tot=0.0,
                       synckey=None).enlazada is False
