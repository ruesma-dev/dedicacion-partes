# tests/test_f062_pipeline_rachas.py
"""F-062 · Las rachas en el registro: contrato, preflight, `ejecutar` y
script (R14, R19, R22, R24, ARCHITECTURE.md#regla-incidencia).

Sin red ni BBDD: la app real con el cliente de los dobles de
`conftest.py` y de `test_f030_pipeline_incidencias.py`. Los `ide` son
inventados y no coinciden con ningún dato real.
"""
from __future__ import annotations

import pytest
from application.services.rachas import (
    CierreRacha,
    LineaVista,
    NoCoincide,
    RachaResumen,
)
from domain.models.registro_models import (
    AccionIncidencia,
    ContextoRachas,
    IncidenciaEntrada,
)

from tests.conftest import OBRA_ORIGEN
from tests.test_f030_pipeline_incidencias import (
    CLAVES_INC,
    ClienteEscribe,
    ClienteInc,
    _json_inc,
    _json_linea,
)
from tests.test_f050_endpoint_propuesta import AJUSTES

#: R22: lo que la respuesta añade cuando la petición trae las claves nuevas.
CLAVES_RACHAS = {"rachas", "cierres_racha", "no_coincide"}


def _app(monkeypatch, cli, pipeline=None):
    """La app real con el cliente `cli` (y, si se da, otro pipeline)."""
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from interface_adapters.api import app as modulo_app

    monkeypatch.setattr(modulo_app, "SigridWriteClient", lambda **kw: cli)
    if pipeline is not None:
        monkeypatch.setattr(modulo_app, "RegistroPipeline", pipeline)
    st = SimpleNamespace(**{**AJUSTES, "sigrid_lecturas_paralelas": 4})
    return TestClient(modulo_app.build_app(st))


@pytest.fixture
def api(monkeypatch):
    return lambda cli: _app(monkeypatch, cli)


def _peticion(**kw):
    return {"obra": {"codigo": OBRA_ORIGEN}, "lineas": [_json_linea(1)],
            "incidencias": [_json_inc()], **kw}


# ============================ contrato (T7) ============================== #
def test_f062_r24_contrato_incidencia_con_su_obra_y_dia_fin_antes():
    from interface_adapters.api.app import IncidenciaIn

    entrada = IncidenciaEntrada(**IncidenciaIn(**_json_inc(
        obra_ide=40, dia_fin_antes=7)).model_dump())
    assert (entrada.obra_ide, entrada.dia_fin_antes) == (40, 7)
    sin = IncidenciaIn(**_json_inc())
    assert (sin.obra_ide, sin.dia_fin_antes) == (None, None)


def test_f062_r24_contrato_las_claves_nuevas_por_defecto_vacias():
    from interface_adapters.api.app import LoteIn, PeticionIn

    p = PeticionIn(**_peticion())
    assert (p.incidencias_mes, p.cierres_recursos, p.quitadas) == ([], [], [])
    lote = LoteIn(peticiones=[_peticion(
        incidencias_mes=[_json_inc(obra_ide=40)], cierres_recursos=[200],
        quitadas=[_json_inc(8, hmores_ide_ini=51)])])
    q = lote.peticiones[0]
    assert ([x.obra_ide for x in q.incidencias_mes], q.cierres_recursos,
            [x.hmores_ide_ini for x in q.quitadas]) == ([40], [200], [51])
    vacio = ContextoRachas()
    assert (vacio.incidencias_mes, vacio.cierres_recursos,
            vacio.quitadas) == ([], [], [])


def test_f062_r22_contrato_sin_las_claves_nuevas_responde_como_f030(api):
    cuerpo = api(ClienteInc()).post("/api/registro/preflight",
                                    json=_peticion()).json()
    assert cuerpo["ok"] is True and not CLAVES_RACHAS & set(cuerpo)
    assert [set(x) for x in cuerpo["incidencias"]] == [CLAVES_INC] * 2
    vacias = api(ClienteInc()).post("/api/registro/preflight", json=_peticion(
        incidencias_mes=[], cierres_recursos=[], quitadas=[])).json()
    assert vacias == cuerpo
    lote = api(ClienteInc()).post("/api/registro/preflight-lote", json={
        "peticiones": [_peticion()]}).json()
    assert not CLAVES_RACHAS & set(lote["obras"][0])
    ej = api(ClienteEscribe()).post("/api/registro/ejecutar",
                                    json=_peticion()).json()
    assert ej["ok"] is True and not CLAVES_RACHAS & set(ej)


def test_f062_r22_contrato_con_las_claves_nuevas_responde_las_rachas(api):
    nuevas = {"incidencias_mes": [_json_inc(obra_ide=40)],
              "cierres_recursos": [200]}
    cuerpo = api(ClienteInc()).post("/api/registro/preflight",
                                    json=_peticion(**nuevas)).json()
    assert cuerpo["ok"] is True and CLAVES_RACHAS <= set(cuerpo)
    assert all(isinstance(cuerpo[k], list) for k in CLAVES_RACHAS)
    lote = api(ClienteInc()).post("/api/registro/preflight-lote", json={
        "peticiones": [_peticion(**nuevas), _peticion()]}).json()
    a, b = lote["obras"]
    assert CLAVES_RACHAS <= set(a) and not CLAVES_RACHAS & set(b)
    solo_cierres = api(ClienteInc()).post("/api/registro/preflight", json={
        "obra": {"codigo": OBRA_ORIGEN}, "lineas": [_json_linea(1)],
        "cierres_recursos": [200]}).json()
    assert CLAVES_RACHAS <= set(solo_cierres)
    ej = api(ClienteEscribe()).post("/api/registro/ejecutar",
                                    json=_peticion(**nuevas)).json()
    assert ej["ok"] is True and CLAVES_RACHAS <= set(ej)


def test_f062_r24_contrato_el_contexto_llega_al_pipeline(monkeypatch):
    llamadas = []

    class Pipeline:
        def __init__(self, *, cliente, settings, contexto=None):
            self.contexto = contexto

        def con_contexto(self, contexto):
            return Pipeline(cliente=None, settings=None, contexto=contexto)

        def preflight(self, **kw):
            llamadas.append({**kw, "contexto": self.contexto})
            raise RuntimeError("solo se mira la llamada")

    app = _app(monkeypatch, ClienteInc(), Pipeline)
    app.post("/api/registro/preflight", json=_peticion(
        incidencias_mes=[_json_inc(obra_ide=40), _json_inc(8)],
        cierres_recursos=[200, 201],
        quitadas=[_json_inc(9, hmores_ide_fin=62, dia_fin_antes=7)]))
    app.post("/api/registro/preflight", json=_peticion())
    con, sin = llamadas
    ctx = con["contexto"]
    assert ([x.id for x in ctx.incidencias_mes], ctx.cierres_recursos,
            [(x.id, x.dia_fin_antes) for x in ctx.quitadas]) == (
        [7, 8], [200, 201], [(9, 7)])
    assert [x.id for x in con["incidencias"]] == [7]
    assert sin["contexto"] is None and set(sin) == {
        "obra", "lineas", "incidencias", "contexto"}
    # `ejecutar` no gana parámetros (F-013 R3): el contexto va en el
    # pipeline.
    from application.pipelines.registro_pipeline import RegistroPipeline

    from tests.conftest import SettingsFalso

    base = RegistroPipeline(cliente=ClienteInc(), settings=SettingsFalso())
    otro = base.con_contexto(ctx)
    assert (otro._contexto, otro._cli, otro._st, base._contexto) == (
        ctx, base._cli, base._st, None)


def test_f062_r22_contrato_la_linea_publica_ajena_y_fec_antes():
    from interface_adapters.api.app import _con_incidencias

    devolver = AccionIncidencia(id=7, rol="devolver", accion="editar",
                                fecha_int=20261007, fec_antes=20261009,
                                hmores_ide=62, ajena=True)
    propia = AccionIncidencia(id=7, rol="fin", accion="editar",
                              fecha_int=20261016, fec_antes=20261009,
                              hmores_ide=52)
    continua = AccionIncidencia(id=8, rol="ini", accion="continua",
                                fecha_int=20261012)
    r = _con_incidencias({}, [devolver, propia, continua])
    assert [set(x) for x in r["incidencias"]] == [
        CLAVES_INC | {"fec_antes", "ajena"}, CLAVES_INC | {"fec_antes"},
        CLAVES_INC]
    assert (r["incidencias"][0]["ajena"], r["incidencias"][0]["rol"]) == (
        True, "devolver")


def test_f062_r22_contrato_rachas_cierres_y_no_coincide_en_json():
    from types import SimpleNamespace

    from interface_adapters.api.app import _con_rachas

    res = SimpleNamespace(
        rachas=[RachaResumen(7, "abre", 20261005, "PT26/1", "cierra",
                             20261016, "PT26/1", 7, ["aviso"])],
        cierres_racha=[CierreRacha(
            200, "CIV", 51, 20260927, "PT26/9", "escribir", 20260930,
            "porcentajes:inc:5:fin", 5, "motivo", parte_cod="PT26/9",
            hmoide=9, obride=40, cenide=7, paride=300, caaide=400,
            hmores_ide=None)],
        no_coincide=[NoCoincide("quitada", 200, 9, [
            LineaVista(51, "CIV", 20261005, "PT26/1")], "m", [51])])

    r = _con_rachas({"ok": True}, res)
    assert r["rachas"] == [{
        "id": 7, "papel": "abre", "inicio_fec": 20261005,
        "inicio_parte": "PT26/1", "cierre": "cierra", "cierre_fec": 20261016,
        "cierre_parte": "PT26/1", "duena_id": 7, "avisos": ["aviso"]}]
    assert r["cierres_racha"] == [{
        "recurso_ide": 200, "codigo": "CIV", "inicio_ide": 51,
        "inicio_fec": 20260927, "inicio_parte": "PT26/9",
        "accion": "escribir", "fecha_int": 20260930, "incidencia_id": 5,
        "motivo": "motivo", "parte_cod": "PT26/9", "hmores_ide": None}]
    assert r["no_coincide"] == [{
        "tipo": "quitada", "recurso_ide": 200, "incidencia_id": 9,
        "lineas": [{"ide": 51, "codigo": "CIV", "fecha_int": 20261005,
                    "parte_cod": "PT26/1"}],
        "motivo": "m", "en_sigrid": [51]}]
    assert _con_rachas({"ok": True}, object()) == {
        "ok": True, "rachas": [], "cierres_racha": [], "no_coincide": []}
