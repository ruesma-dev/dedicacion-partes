# tests/test_f069_tex_registrada.py
"""F-069 · T20 (D20; R24, R26-R28; design §6.5 y §7.1): el comentario de
una línea YA registrada llega a Sigrid cambiando solo su `tex`.

- Paso 6: `lineas_registradas` trae, en la misma lectura y solo si algo
  trae comentario, `tex`, `obride` y el `con.est` de su parte (sin
  comentarios, la lectura de hoy, R24). `tex_a_actualizar` decide el
  `tex_nuevo`; la acción sigue siendo `ya_registrado` y su motivo dice «se
  actualiza el comentario» o por qué no.
- `ejecutar`: relee esas líneas (`lineas_para_editar`) y, si siguen
  valiendo, `stmt_editar_tex` (`UPDATE hmores SET tex = ?` con la guarda de
  F-051 y, en pruebas, `AND obride = ?`); nunca `DELETE`, ni `can`, `pre`
  ni `tot`. La respuesta lleva `tex_actualizadas`.

Sin red ni BBDD; los `ide` son inventados. Ninguna escritura real: las
sentencias se acumulan en el doble.
"""
from __future__ import annotations

from dataclasses import asdict, replace

import pytest
from application.pipelines.registro_lote import RegistroLote
from application.pipelines.registro_pipeline import RegistroPipeline
from application.services.texto_linea import (
    MOTIVO_TEX_CERRADO,
    MOTIVO_TEX_FUERA_PRUEBAS,
    MOTIVO_TEX_NO_NUESTRA,
    MOTIVO_TEX_SE_ACTUALIZA,
    hay_comentarios,
    tex_a_actualizar,
)
from domain.models.registro_models import LineaSigrid, ObraEntrada

from tests.conftest import OBRA_ORIGEN, SettingsFalso
from tests.test_f055_lote import _ajustes
from tests.test_f069_pipeline_importe import (
    ClienteCant,
    _caja,
    _km,
    _titular,
)

#: La obra de pruebas del doble (`ClienteFalso.obra`) y la de origen.
OBRA_PRUEBAS_IDE = 828942
OBRA_ORIGEN_IDE = 555001


def _reg(ide: int, reside: int, synckey: str | None, tex: str | None, *,
         horide: int = 5, hora: str = "MENC", can: float = 0.4,
         obride: int | None = OBRA_PRUEBAS_IDE) -> LineaSigrid:
    return LineaSigrid(ide=ide, reside=reside, fecha_int=20260731,
                       horide=horide, hora_codigo=hora, can=can, tot=1.0,
                       synckey=synckey, paride=80001, tex=tex,
                       obride=obride)


def _registradas(*, tex_titular="PRUEBA-PORC viejo", tex_km="PRUEBA-PORC",
                 tex_caja="PRUEBA-PORC", obride=OBRA_PRUEBAS_IDE,
                 sk_titular="porcentajes:1"):
    return [
        _reg(5301, 200, sk_titular, tex_titular, obride=obride),
        _reg(5302, 20, "porcentajes:vin:1:20", tex_km, horide=41,
             hora="KM", obride=obride),
        _reg(5303, 22, "porcentajes:vin:1:22", tex_caja, horide=43,
             hora="CO", can=1.0, obride=obride)]


def _entrada(comentario="nuevo", km="km nuevo", caja="caja nueva"):
    return _titular(hmores_ide=5301, comentario=comentario, vinculados=[
        _km(hmores_ide=5302, comentario=km),
        _caja(hmores_ide=5303, comentario=caja)])


def _st(real: bool) -> SettingsFalso:
    return SettingsFalso(obra_pruebas_forzar=not real)


def _pf(cli, *lineas_, real=False):
    return RegistroPipeline(cliente=cli, settings=_st(real)).preflight(
        obra=ObraEntrada(codigo=OBRA_ORIGEN), lineas=list(lineas_))


def _eje(cli, *lineas_, real=False):
    return RegistroPipeline(cliente=cli, settings=_st(real)).ejecutar(
        obra=ObraEntrada(codigo=OBRA_ORIGEN), lineas=list(lineas_),
        pisar_claves=set())


def _sentencias(cli) -> list[dict]:
    return [s for x in cli.llamadas for s in x]


# ====================== la decisión, pura (§6.5) ========================= #
def test_f069_r26_tex_a_actualizar():
    hit = _reg(1, 200, "porcentajes:1", "  PRUEBA-PORC viejo ")
    kw = dict(en_registro=True, obride_pruebas=OBRA_PRUEBAS_IDE)
    assert tex_a_actualizar("nuevo", "PRUEBA-PORC", hit, **kw) == (
        "PRUEBA-PORC nuevo", MOTIVO_TEX_SE_ACTUALIZA)
    assert tex_a_actualizar(" viejo ", "PRUEBA-PORC", hit, **kw) == (
        None, None)                                 # igual: nada
    assert tex_a_actualizar(None, "PRUEBA-PORC", hit, **kw) == (None, None)
    assert tex_a_actualizar("  ", "PRUEBA-PORC", hit, **kw) == (None, None)
    ajena = replace(hit, synckey="partes:77")
    assert tex_a_actualizar("nuevo", "PRUEBA-PORC", ajena, **kw) == (
        None, MOTIVO_TEX_NO_NUESTRA)
    sin_sk = replace(hit, synckey=None)
    assert tex_a_actualizar("nuevo", "PRUEBA-PORC", sin_sk, **kw) == (
        None, MOTIVO_TEX_NO_NUESTRA)
    assert tex_a_actualizar("nuevo", "PRUEBA-PORC", hit, en_registro=False,
                            obride_pruebas=OBRA_PRUEBAS_IDE) == (
        None, MOTIVO_TEX_CERRADO)
    otra = replace(hit, obride=OBRA_ORIGEN_IDE)
    assert tex_a_actualizar("nuevo", "PRUEBA-PORC", otra, **kw) == (
        None, MOTIVO_TEX_FUERA_PRUEBAS)
    # En real no hay obra de pruebas que mirar ni marca.
    real = replace(hit, tex="viejo", obride=OBRA_ORIGEN_IDE)
    assert tex_a_actualizar("nuevo", None, real, en_registro=True,
                            obride_pruebas=None) == (
        "nuevo", MOTIVO_TEX_SE_ACTUALIZA)
    assert tex_a_actualizar("viejo", None, real, en_registro=True,
                            obride_pruebas=None) == (None, None)


def test_f069_r24_hay_comentarios():
    assert not hay_comentarios([_titular(), _titular(vinculados=[_km()])])
    assert not hay_comentarios([_titular(comentario="  ")])
    assert hay_comentarios([_titular(comentario="x")])
    assert hay_comentarios([_titular(vinculados=[_km(comentario="x")])])


# ======================== paso 6 · el preflight ========================== #
def test_f069_r26_preflight_titular_km_y_caja_con_tex_nuevo():
    cli = ClienteCant(lineas_parte=_registradas())
    pf = _pf(cli, _entrada())
    [a] = pf.acciones
    assert (a.accion, a.hmores_ide, a.tex_nuevo) == (
        "ya_registrado", 5301, "PRUEBA-PORC nuevo")
    assert a.motivo.endswith("; " + MOTIVO_TEX_SE_ACTUALIZA)
    por = {v.recurso_ide: v for v in pf.vinculados}
    assert [(por[r].accion, por[r].tex_nuevo) for r in (20, 22)] == [
        ("ya_registrado", "PRUEBA-PORC km nuevo"),
        ("ya_registrado", "PRUEBA-PORC caja nueva")]
    assert por[22].motivo.endswith(MOTIVO_TEX_SE_ACTUALIZA)
    # Una sola lectura de lo registrado, con el `tex` (kw `con_tex`).
    assert cli.registradas_con_tex[:1] == [True]


def test_f069_r24_sin_comentario_la_lectura_de_hoy_y_nada():
    cli = ClienteCant(lineas_parte=_registradas())
    pf = _pf(cli, _entrada(comentario=None, km=None, caja=None))
    assert cli.registradas_con_tex == [False]
    assert [a.tex_nuevo for a in pf.acciones] == [None]
    assert [v.tex_nuevo for v in pf.vinculados] == [None, None]
    assert not any("comentario" in (a.motivo or "") for a in pf.acciones)


def test_f069_r26_igual_no_cambia_y_no_dice_nada():
    cli = ClienteCant(lineas_parte=_registradas(
        tex_titular="PRUEBA-PORC nuevo", tex_km="PRUEBA-PORC km nuevo",
        tex_caja=" PRUEBA-PORC caja nueva "))
    pf = _pf(cli, _entrada())
    assert [a.tex_nuevo for a in pf.acciones] == [None]
    assert [v.tex_nuevo for v in pf.vinculados] == [None, None]
    assert pf.acciones[0].motivo.endswith("no se duplica")
    res = _eje(cli, _entrada())
    assert res.tex_actualizadas == []
    assert _sentencias(cli) == []


def test_f069_r26_parte_cerrado_no_se_toca_y_dice_por_que():
    cli = ClienteCant(lineas_parte=_registradas())
    cli.parte_est = 3
    pf = _pf(cli, _entrada())
    assert [a.tex_nuevo for a in pf.acciones] == [None]
    assert pf.acciones[0].motivo.endswith(MOTIVO_TEX_CERRADO)
    assert {v.motivo.split("; ")[-1] for v in pf.vinculados} == {
        MOTIVO_TEX_CERRADO}


def test_f069_r26_linea_que_no_es_nuestra_no_se_toca():
    cli = ClienteCant(lineas_parte=_registradas(sk_titular=None))
    pf = _pf(cli, _entrada())
    [a] = pf.acciones
    assert (a.accion, a.tex_nuevo) == ("ya_registrado", None)
    assert a.motivo.endswith(MOTIVO_TEX_NO_NUESTRA)
    res = _eje(cli, _entrada())
    assert 5301 not in [s["parameters"]["ide"] for s in _sentencias(cli)]
    assert [t["hmores_ide"] for t in res.tex_actualizadas] == [5302, 5303]


def test_f069_r26_en_pruebas_otra_obra_no_se_toca():
    cli = ClienteCant(lineas_parte=_registradas(obride=OBRA_ORIGEN_IDE))
    pf = _pf(cli, _entrada())
    assert [a.tex_nuevo for a in pf.acciones] == [None]
    assert pf.acciones[0].motivo.endswith(MOTIVO_TEX_FUERA_PRUEBAS)
    res = _eje(cli, _entrada())
    assert res.tex_actualizadas == [] and _sentencias(cli) == []


def test_f069_r26_titular_omitido_su_vinculado_sin_tex_nuevo():
    """`cerrar`: el vinculado de un titular omitido no se actualiza."""
    cli = ClienteCant(lineas_parte=_registradas())
    pf = _pf(cli, replace(_entrada(), recurso_ide=None))
    assert [a.accion for a in pf.acciones] == ["omitir"]
    assert {(v.accion, v.tex_nuevo) for v in pf.vinculados} == {
        ("omitir", None)}


# ========================= paso 10 · ejecutar ============================ #
def test_f069_r26_ejecutar_solo_cambia_el_tex_en_pruebas():
    cli = ClienteCant(lineas_parte=_registradas())
    res = _eje(cli, _entrada())
    ss = _sentencias(cli)
    assert {s["sql"] for s in ss} == {"editar_tex"}
    assert [(s["parameters"]["ide"], s["parameters"]["tex"],
             s["parameters"]["obride"], s["parameters"]["hora"])
            for s in ss] == [
        (5301, "PRUEBA-PORC nuevo", OBRA_PRUEBAS_IDE, None),
        (5302, "PRUEBA-PORC km nuevo", OBRA_PRUEBAS_IDE, "KM"),
        (5303, "PRUEBA-PORC caja nueva", OBRA_PRUEBAS_IDE, "CO")]
    for s in ss:                       # la guarda de F-051 con lo releído
        p = s["parameters"]
        assert set(p) == {"ide", "reside", "can_leido", "synckey_leida",
                          "tex", "hora", "obride"}
    assert res.tex_actualizadas == [
        {"registro_id": 1, "hmores_ide": 5301, "tex": "PRUEBA-PORC nuevo"},
        {"registro_id": 1, "vinculado_ide": 20, "hmores_ide": 5302,
         "tex": "PRUEBA-PORC km nuevo"},
        {"registro_id": 1, "vinculado_ide": 22, "hmores_ide": 5303,
         "tex": "PRUEBA-PORC caja nueva"}]
    # Ni `can` ni `tot` cambian; el `tex`, sí (el doble aplica la guarda).
    por = {ls.ide: ls for ls in cli.lineas_parte}
    assert [(por[i].can, por[i].tot) for i in (5301, 5302, 5303)] == [
        (0.4, 1.0), (0.4, 1.0), (1.0, 1.0)]
    assert por[5302].tex == "PRUEBA-PORC km nuevo"
    assert cli.borrados() == []
    assert res.escritas == [] and res.editadas == []
    assert [v.accion for v in res.vinculados] == ["ya_registrado"] * 2


def test_f069_r26_ejecutar_en_real_sin_marca_ni_obride():
    cli = ClienteCant(lineas_parte=_registradas(
        tex_titular="viejo", tex_km=None, tex_caja=None,
        obride=OBRA_ORIGEN_IDE))
    res = _eje(cli, _entrada(km=None, caja=None), real=True)
    [s] = _sentencias(cli)
    assert (s["sql"], s["parameters"]["tex"], s["parameters"]["obride"]) == (
        "editar_tex", "nuevo", None)
    assert [t["tex"] for t in res.tex_actualizadas] == ["nuevo"]


def test_f069_r26_relectura_que_ya_no_vale_no_se_escribe():
    cli = ClienteCant(lineas_parte=_registradas())
    pf = _pf(cli, _entrada())
    assert pf.acciones[0].tex_nuevo is not None
    # Entre el preflight y la escritura, la del km pasa a otra `synckey` y
    # la caja gana un enlace: solo el titular se actualiza.
    cli.lineas_parte[1] = replace(cli.lineas_parte[1], synckey="partes:1")
    cli.enlazadas = frozenset({5303})
    res = _eje(cli, _entrada())
    assert [s["parameters"]["ide"] for s in _sentencias(cli)] == [5301]
    assert [t["hmores_ide"] for t in res.tex_actualizadas] == [5301]


def test_f069_r26_la_guarda_no_deja_y_no_sale_en_tex_actualizadas():
    cli = ClienteCant(lineas_parte=_registradas())
    cli.guarda_falla = frozenset({5302})
    res = _eje(cli, _entrada())
    assert [s["parameters"]["ide"] for s in _sentencias(cli)] == [
        5301, 5302, 5303]
    assert [t["hmores_ide"] for t in res.tex_actualizadas] == [5301, 5303]


def test_f069_r26_con_otra_escritura_en_la_misma_peticion():
    """Un titular que se escribe y otro ya registrado con comentario: el
    `INSERT` del primero y el `UPDATE` del `tex` del segundo, sin
    `DELETE`."""
    cli = ClienteCant(lineas_parte=_registradas())
    nueva = _titular(registro_id=2, recurso_ide=400, nombre="Otro",
                     categoria="Jefe de obra", comentario="otra")
    res = _eje(cli, _entrada(km=None, caja=None), nueva)
    ss = _sentencias(cli)
    assert [(s["sql"], s["parameters"].get("synckey"),
             s["parameters"].get("ide")) for s in ss
            if s["sql"] in ("insert", "editar_tex")] == [
        ("insert", "porcentajes:2", None), ("editar_tex", None, 5301)]
    assert [e["registro_id"] for e in res.escritas] == [2]
    assert [t["hmores_ide"] for t in res.tex_actualizadas] == [5301]
    assert cli.borrados() == []


def test_f069_r26_el_lote_del_tex_es_el_ultimo_del_ejecutar():
    """Design §6.5 (decisión 8 del implementer; review 4, O1): el `UPDATE
    hmores SET tex` va en un lote propio y DESPUÉS de todas las demás
    escrituras: el `INSERT` del titular nuevo y el de su vinculado
    (`EscrituraVinculados`) van antes."""
    cli = ClienteCant(lineas_parte=_registradas())
    nueva = _titular(registro_id=2, recurso_ide=400, nombre="Otro",
                     categoria="Jefe de obra", comentario="otra",
                     vinculados=[_km(comentario="km de otra")])
    res = _eje(cli, _entrada(km=None, caja=None), nueva)
    lotes = [[(s["sql"], s["parameters"].get("synckey")) for s in lote]
             for lote in cli.llamadas]
    assert lotes == [[("insert", "porcentajes:2")],
                     [("insert", "porcentajes:vin:2:20")],
                     [("editar_tex", None)]]
    assert [v.accion for v in res.vinculados] == [
        "ya_registrado", "ya_registrado", "escribir"]
    assert [t["hmores_ide"] for t in res.tex_actualizadas] == [5301]


# ===================== R27 · suelto = lote; R28 · contrato =============== #
def test_f069_r27_el_lote_da_lo_mismo_que_la_suelta():
    peticion = (ObraEntrada(codigo=OBRA_ORIGEN), [_entrada()])
    suelto = _pf(ClienteCant(lineas_parte=_registradas()), *peticion[1])
    cli = ClienteCant(lineas_parte=_registradas())
    [lote] = RegistroLote(cliente=cli, settings=_ajustes()).preflight(
        [peticion])
    assert [asdict(a) for a in lote.acciones] == [
        asdict(a) for a in suelto.acciones]
    assert [asdict(v) for v in lote.vinculados] == [
        asdict(v) for v in suelto.vinculados]
    assert cli.registradas_con_tex == [True]


def test_f069_r28_respuestas_con_tex_nuevo_y_tex_actualizadas(monkeypatch):
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from interface_adapters.api import app as modulo_app

    from tests.test_f050_endpoint_propuesta import AJUSTES

    def vin(recurso_ide, tipo, unidad, reparto, cantidad, hmores_ide, com):
        return {"recurso_ide": recurso_ide, "tipo": tipo, "cod": tipo,
                "paride": 81001, "partida_cod": "CICO13",
                "hmores_ide": hmores_ide, "importe_mensual": True,
                "unidad": unidad, "reparto": reparto, "cantidad": cantidad,
                "copiado": False, "comentario": com,
                "precio_km": 0.2 if unidad == "km" else None}

    cuerpo = {"obra": {"codigo": OBRA_ORIGEN}, "lineas": [{
        "registro_id": 1, "ano": 2026, "mes": 7, "porcentaje": 0.4,
        "recurso_ide": 200, "empresa": 1, "paride": 80001,
        "partida_cod": "CI.1.10", "hmores_ide": 5301, "comentario": "nuevo",
        "vinculados": [vin(20, "VP", "km", "pct", 100.0, 5302, "km nuevo"),
                       vin(22, "CAJA", "eur", "obra", 80.0, 5303,
                           "caja nueva")]}]}
    cli = ClienteCant(lineas_parte=_registradas())
    monkeypatch.setattr(modulo_app, "SigridWriteClient", lambda **kw: cli)
    ajustes = SimpleNamespace(**AJUSTES, sigrid_lecturas_paralelas=4)
    c = TestClient(modulo_app.build_app(ajustes))
    pre = c.post("/api/registro/preflight", json=cuerpo).json()
    assert pre["acciones"][0]["tex_nuevo"] == "PRUEBA-PORC nuevo"
    assert [v["tex_nuevo"] for v in pre["vinculados"]] == [
        "PRUEBA-PORC km nuevo", "PRUEBA-PORC caja nueva"]
    eje = c.post("/api/registro/ejecutar", json=cuerpo).json()
    assert [t["hmores_ide"] for t in eje["tex_actualizadas"]] == [
        5301, 5302, 5303]
    sin = {**cuerpo, "lineas": [{**cuerpo["lineas"][0], "comentario": None,
                                 "vinculados": []}]}
    assert c.post("/api/registro/ejecutar", json=sin).json()[
        "tex_actualizadas"] == []


# ========================= el SQL de Sigrid (§7.1) ======================= #
class _Lector:
    """`SigridWriteClient` con `_lectura` anotada (sin red)."""

    def __init__(self, filas):
        from infrastructure.sigrid.sigrid_write_client import SigridWriteClient

        self.cli = SigridWriteClient(base_url="http://sigrid.invalid",
                                     function_key="sin-clave",
                                     database="ruesma")
        self.llamadas: list[tuple[str, list]] = []

        def _lectura(nombre, sql, params):
            self.llamadas.append((sql, params))
            return [dict(f) for f in filas]

        self.cli._lectura = _lectura


FILA_REG = {"ide": 5301, "hmoide": 777, "reside": 200, "fec": 20260731,
            "horide": 5, "paride": 80001, "hora": "MENC", "can": 0.4,
            "tot": 1.0, "synckey": "porcentajes:1"}


def test_f069_r24_lineas_registradas_sin_con_tex_la_sql_de_hoy():
    lec = _Lector([FILA_REG])
    lec.cli.lineas_registradas(["porcentajes:1"], [5301])
    [(sql, _)] = lec.llamadas
    assert "tex" not in sql and "obride" not in sql and "con." not in sql


def test_f069_r26_lineas_registradas_con_tex_en_la_misma_lectura():
    lec = _Lector([{**FILA_REG, "tex": " PRUEBA-PORC x ",
                    "obride": OBRA_PRUEBAS_IDE, "est": 1}])
    por_sk, por_ide = lec.cli.lineas_registradas(
        ["porcentajes:1"], [], con_tex=True)
    [(sql, params)] = lec.llamadas
    assert ("CAST(hmores.tex AS NVARCHAR(400)) AS tex, "
            "hmores.obride AS obride, con.est AS est ") in sql
    assert "LEFT JOIN con ON con.ide = hmores.hmoide " in sql
    assert params == ["porcentajes:1"]
    ls = por_sk["porcentajes:1"]
    assert (ls.tex, ls.obride, ls.parte_est, ls.hmoide) == (
        " PRUEBA-PORC x ", OBRA_PRUEBAS_IDE, 1, 777)
    lec = _Lector([{**FILA_REG, "tex": None, "obride": None, "est": None}])
    _, por_ide = lec.cli.lineas_registradas([], [5301], con_tex=True)
    assert (por_ide[5301].obride, por_ide[5301].parte_est) == (None, None)


@pytest.mark.parametrize("obride, hora", [(None, None), (OBRA_PRUEBAS_IDE,
                                                         "KM")])
def test_f069_r26_stmt_editar_tex(obride, hora):
    from infrastructure.sigrid.sigrid_write_client import SigridWriteClient

    cli = SigridWriteClient(base_url="http://sigrid.invalid",
                            function_key="sin-clave", database="ruesma")
    s = cli.stmt_editar_tex(ide=5301, reside=200, can_leido=0.4,
                            synckey_leida=" porcentajes:1 ", tex="nuevo",
                            hora=hora, obride=obride)
    guarda, params = cli._guarda(5301, 200, 0.4, " porcentajes:1 ", hora)
    extra = " AND obride = ?" if obride else ""
    assert s["sql"] == f"UPDATE hmores SET tex = ? {guarda}{extra}"
    assert s["parameters"] == ["nuevo", *params] + (
        [OBRA_PRUEBAS_IDE] if obride else [])
    assert "DELETE" not in s["sql"].upper()
    for campo in ("can =", "pre =", "tot =", "horide =", "paride =",
                  "caaide ="):
        assert campo not in s["sql"].split("WHERE")[0]
