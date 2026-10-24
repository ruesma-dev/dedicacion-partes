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
    st = SimpleNamespace(**{**AJUSTES, "sigrid_lecturas_paralelas": 4,
                            "incidencias_meses_atras": 12})
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


# ============================ preflight (T9) ============================= #
from application.pipelines.registro_pipeline import RegistroPipeline
from domain.models.registro_models import (
    HoraRecurso,
    LineaIncidenciaSigrid,
    ObraEntrada,
)

from tests.conftest import EMPRESA, SettingsFalso, linea

OBRA = ObraEntrada(codigo=OBRA_ORIGEN)
SK_INI, SK_FIN = "porcentajes:inc:7:ini", "porcentajes:inc:7:fin"


def _inc(i=7, desde=5, hasta=9, codigo="CIV", *, mes=10, **kw):
    datos = {"id": i, "recurso_ide": 200, "empresa": EMPRESA,
             "codigo": codigo, "ano": 2026, "mes": mes, "desde": desde,
             "hasta": hasta, "paride": 0, "obra_ide": 555001, **kw}
    return IncidenciaEntrada(**datos)


def _l(ide, fec, cod="CIV", *, sk=None, parte="PT26/00040", hmoide=640,
       est=1, reside=200, can=0.0, **kw):
    return LineaIncidenciaSigrid(ide, reside, fec, cod, sk, parte, can=can,
                                 hmoide=hmoide, parte_est=est, **kw)


def _cli(lineas=(), cls=ClienteInc):
    cli = cls()
    cli.lineas_incidencia = list(lineas)
    cli.horas[200] = [*cli.horas[200], HoraRecurso(72, "CIE", "Baja(B)", 0.0)]
    return cli


def _pf(cli, incs, *, lineas=(), contexto=None, pruebas=False):
    pipe = RegistroPipeline(cliente=cli, settings=SettingsFalso(
        obra_pruebas_forzar=pruebas), contexto=contexto)
    return pipe.preflight(obra=OBRA, lineas=list(lineas),
                          incidencias=list(incs))


def _v(pf):
    return [(a.id, a.rol, a.accion, a.fecha_int, a.parte_cod)
            for a in pf.incidencias]


def test_f062_c1_preflight_abre_y_cierra_en_el_parte_del_periodo():
    cli = _cli()
    pf = _pf(cli, [_inc()])
    assert _v(pf) == [(7, "ini", "escribir", 20261005, "PT26/00251"),
                      (7, "fin", "escribir", 20261009, "PT26/00251")]
    assert [(r.id, r.papel, r.cierre, r.cierre_fec) for r in pf.rachas] == [
        (7, "abre", "cierra", 20261009)]
    # R19: UNA lectura, M−12 a M+1, de sus recursos, en real sin obra.
    assert cli.leidas_ventana == [([200], 20251001, 20261130, None, [])]
    assert (pf.cierres_racha, pf.no_coincide) == ([], [])


def test_f062_c2_preflight_dos_rachas_o_una_que_se_alarga():
    pf = _pf(_cli(), [_inc(7, 5, 9), _inc(8, 13, 16)])
    assert [a.accion for a in pf.incidencias] == ["escribir"] * 4
    hecha = [_l(51, 20261005, sk=SK_INI, hmoide=777, parte="PT26/00251"),
             _l(52, 20261009, "CIZ", sk=SK_FIN, hmoide=777,
                parte="PT26/00251")]
    traza = {"hmores_ide_ini": 51, "dia_ini": 5, "hmores_ide_fin": 52,
             "dia_fin": 9}
    pf = _pf(_cli(hecha), [_inc(7, 5, 9, **traza), _inc(8, 12, 16)])
    assert [(a.id, a.rol, a.accion, a.fecha_int, a.fec_antes, a.hmores_ide)
            for a in pf.incidencias] == [
        (7, "ini", "ya_registrado", 20261005, None, 51),
        (7, "fin", "editar", 20261016, 20261009, 52),
        (8, "ini", "continua", 20261012, None, None),
        (8, "fin", "continua", 20261016, None, None)]
    assert [(r.id, r.papel, r.cierre) for r in pf.rachas] == [
        (7, "abre", "cierra"), (8, "continua", "cadena")]


def test_f062_c3_preflight_fin_de_mes_abierta_y_noviembre_continua():
    pf = _pf(_cli(), [_inc(7, 27, 31)])
    assert [a.accion for a in pf.incidencias] == ["escribir", "abierta"]
    octubre = [_l(51, 20261027, sk=SK_INI, hmoide=777, parte="PT26/00251")]
    pf = _pf(_cli(octubre), [_inc(9, 2, 6, mes=11)])
    assert _v(pf) == [(9, "ini", "continua", 20261102, "PT26/00251"),
                      (9, "fin", "escribir", 20261106, "PT26/00251")]
    assert pf.incidencias[1].hmoide_destino is None     # el del paso 5


def test_f062_c5_preflight_un_mes_entero_de_baja_no_escribe_nada():
    sep = [_l(51, 20260915, "CIE", sk="porcentajes:inc:3:ini")]
    pf = _pf(_cli(sep), [_inc(7, 1, 31, "CIE")])
    assert [a.accion for a in pf.incidencias] == ["continua", "abierta"]
    assert pf.partes == []


def test_f062_c6_preflight_mueve_el_ciz_de_administracion_de_otra_obra():
    adm = [_l(61, 20261005, obride=40, parte_emp=1),
           _l(62, 20261007, "CIZ", obride=40, parte_emp=1, can=1.0)]
    pf = _pf(_cli(adm), [_inc(7, 5, 9)])
    ini, fin = pf.incidencias
    assert (ini.accion, fin.accion, fin.hmores_ide, fin.fec_antes,
            fin.ajena, fin.can_leido, fin.parte_cod) == (
        "continua", "editar", 62, 20261007, True, 1.0, "PT26/00040")


def test_f062_r5_preflight_el_ciz_va_al_parte_del_inicio():
    adm = [_l(61, 20261001, obride=40, cenide=4, paride=300, caaide=400,
              parte_emp=1)]
    pf = _pf(_cli(adm), [_inc(7, 5, 9)])
    ini, fin = pf.incidencias
    assert (ini.accion, fin.accion, fin.hmoide_destino, fin.parte_cod,
            fin.obride, fin.cenide, fin.paride, fin.caa_ide) == (
        "continua", "escribir", 640, "PT26/00040", 40, 4, 300, 400)
    assert pf.partes == []                  # no pide parte del periodo


def test_f062_c7_preflight_otra_en_el_tramo_omite():
    pf = _pf(_cli([_l(61, 20261007, "CIE")]), [_inc(7, 5, 9)])
    assert [a.accion for a in pf.incidencias] == ["omitir", "omitir"]
    assert pf.partes == []


def test_f062_c4_preflight_cierra_el_mes_anterior_del_designado():
    octubre = [_l(51, 20261027, sk="porcentajes:inc:5:ini", hmoide=777,
                  parte="PT26/00251", obride=555001, cenide=555101,
                  paride=0, caaide=0, parte_emp=1)]
    cli = _cli(octubre)
    pf = _pf(cli, [], lineas=[linea(registro_id=1, mes=11)],
             contexto=ContextoRachas(cierres_recursos=[200]))
    [c] = pf.cierres_racha
    assert (c.accion, c.fecha_int, c.hmoide, c.synckey, c.incidencia_id,
            c.hora_ide) == ("escribir", 20261031, 777,
                            "porcentajes:inc:5:fin", 5, 79)
    assert cli.leidas_ventana == [([200], 20251101, 20261231, None, [])]


class _CuentaPartes(ClienteInc):
    def partes_de_periodos(self, obrides, periodos):
        self.periodos_leidos = [(sorted(obrides), sorted(periodos))]
        return super().partes_de_periodos(obrides, periodos)


def test_f062_c12_preflight_d14_lee_los_partes_de_m1_solo_si_hace_falta():
    sep = [_l(51, 20260915, sk="porcentajes:inc:3:ini", obride=555001,
              cenide=555101, paride=0, caaide=0, parte_emp=1)]
    cli = _cli(sep, _CuentaPartes)
    pf = _pf(cli, [], lineas=[linea(registro_id=1, mes=11)],
             contexto=ContextoRachas(cierres_recursos=[200]))
    [c] = pf.cierres_racha
    assert (c.accion, c.fecha_int, c.hmoide, c.parte_cod) == (
        "escribir", 20261031, 777, "PT26/00251")
    assert cli.periodos_leidos == [([555001], [(2026, 10)])]
    cli = _cli([_l(51, 20261027, sk="x", parte_emp=1)], _CuentaPartes)
    _pf(cli, [], lineas=[linea(registro_id=1, mes=11)],
        contexto=ContextoRachas(cierres_recursos=[200]))
    assert not hasattr(cli, "periodos_leidos")


def test_f062_r12_preflight_cierre_sin_ciz_en_reshor_solo_avisa():
    adm = [_l(51, 20261027, reside=100, parte_emp=1)]
    pf = _pf(_cli(adm), [], lineas=[linea(registro_id=1, mes=11, recurso_ide=100)],
             contexto=ContextoRachas(cierres_recursos=[100]))
    [c] = pf.cierres_racha
    assert (c.accion, c.motivo) == (
        "aviso", ("el recurso no tiene en Sigrid el tipo de hora CIZ: no "
                  "se escribe la incidencia (ni su inicio ni su fin)"))


def test_f062_c10_c11_preflight_no_coincide_quitadas_y_solo_sigrid():
    quitada = _inc(8, 20, 22, hmores_ide_ini=81, dia_ini=20,
                   hmores_ide_fin=82, dia_fin=22)
    lineas = [_l(81, 20261020, sk="porcentajes:inc:8:ini"),
              _l(82, 20261022, "CIZ", sk="porcentajes:inc:8:fin"),
              _l(91, 20261026, "CIE"), _l(92, 20261028, "CIZ")]
    cli = _cli(lineas)
    pf = _pf(cli, [_inc()], contexto=ContextoRachas(
        incidencias_mes=[_inc()], cierres_recursos=[200],
        quitadas=[quitada]))
    assert [(n.tipo, n.incidencia_id, [x.ide for x in n.lineas])
            for n in pf.no_coincide] == [
        ("quitada", 8, [81, 82]), ("solo_sigrid", None, [91, 92])]
    assert cli.leidas_ventana[0][4] == [81, 82]
    # Sin designar, solo la quitada.
    pf = _pf(_cli(lineas), [_inc()], contexto=ContextoRachas(
        incidencias_mes=[_inc()], quitadas=[quitada]))
    assert [n.tipo for n in pf.no_coincide] == ["quitada"]


def test_f062_r19_preflight_en_pruebas_solo_la_obra_de_pruebas():
    cli = _cli()
    _pf(cli, [_inc()], pruebas=True)
    assert cli.leidas_ventana == [([200], 20251001, 20261130, 828942, [])]


def test_f062_r26_preflight_sin_nada_que_escribir_no_lee():
    cli = _cli()
    pf = _pf(cli, [_inc(7, 5, 9, "CIX")], lineas=[linea(registro_id=1, mes=10)])
    assert [a.accion for a in pf.incidencias] == ["omitir", "omitir"]
    assert not hasattr(cli, "leidas_ventana") and pf.rachas == []


def test_f062_r26_preflight_las_lineas_de_porcentaje_deciden_igual():
    from dataclasses import asdict

    sin = _pf(_cli(), [], lineas=[linea(registro_id=1, mes=10), linea(registro_id=2, mes=10)])
    con = _pf(_cli([_l(61, 20261007, "CIE")]), [_inc(), _inc(8, 12, 16)],
              lineas=[linea(registro_id=1, mes=10), linea(registro_id=2, mes=10)],
              contexto=ContextoRachas(cierres_recursos=[200]))
    assert [asdict(a) for a in con.acciones] == [asdict(a)
                                                 for a in sin.acciones]


def test_f062_r19_preflight_si_la_lectura_falla_la_peticion_falla():
    class Falla(ClienteInc):
        def incidencias_en_ventana(self, *a, **kw):
            raise RuntimeError("sigrid-api devolvio una respuesta truncada")

    with pytest.raises(RuntimeError, match="truncada"):
        _pf(_cli(cls=Falla), [_inc()])
