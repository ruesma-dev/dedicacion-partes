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
        "motivo": "motivo", "parte_cod": "PT26/9", "hmores_ide": None,
        "requiere_confirmar": False, "clave": None}]
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


# ============================ ejecutar (T10) ============================= #
from dataclasses import replace as _replace

from domain.models.registro_models import LineaSigrid


class ClienteRachas(ClienteEscribe):
    """`ClienteEscribe` en el que ``lineas_incidencia`` es Sigrid: la
    relectura de `ejecutar` (`lineas_para_editar`) y la de después
    (`lineas_registradas`) las ven; `escribir` aplica el `UPDATE` de la
    `fec` con su guarda (como el SQL: recurso, código, `can` y `synckey`
    leídos, `fec` leída, sin enlaces y parte En registro) y cada `INSERT`
    de una `CI*`/`CIZ` queda como una línea más (para repetir, C9)."""

    def __init__(self, lineas=(), **kw) -> None:
        super().__init__(**kw)
        self.lineas_incidencia = list(lineas)
        self.horas[200] = [*self.horas[200],
                           HoraRecurso(72, "CIE", "Baja(B)", 0.0)]
        self.enlazadas_inc: set[int] = set()

    def _como_linea(self, x) -> LineaSigrid:
        return LineaSigrid(
            ide=x.ide, reside=x.reside, fecha_int=x.fecha_int, horide=None,
            hora_codigo=x.hora_codigo, can=x.can, tot=0.0, synckey=x.synckey,
            hmoide=x.hmoide, parte_cod=x.parte_cod, parte_est=x.parte_est,
            enlazada=x.ide in self.enlazadas_inc)

    def lineas_para_editar(self, ides):
        out = super().lineas_para_editar(ides)
        out.update({x.ide: self._como_linea(x) for x in self.lineas_incidencia
                    if x.ide in set(ides)})
        return out

    def lineas_registradas(self, claves, ides=()):
        por_sk, por_ide = super().lineas_registradas(claves, ides)
        pedidos = {int(i) for i in ides if i}
        por_ide.update({x.ide: self._como_linea(x)
                        for x in self.lineas_incidencia if x.ide in pedidos})
        return por_sk, por_ide

    def _cod(self, horide):
        return next(h.cod for hs in self.horas.values() for h in hs
                    if h.horide == horide)

    def escribir(self, statements):
        n = super().escribir(statements)
        for s in statements:
            kw = s["parameters"]
            if s["sql"] == "editar_fec":
                for i, x in enumerate(self.lineas_incidencia):
                    if (x.ide == kw["ide"] and x.parte_est == 1
                            and x.ide not in self.enlazadas_inc
                            and x.fecha_int == kw["fec_leida"]
                            and x.reside == kw["reside"]
                            and x.hora_codigo == kw["hora_codigo"]
                            and abs(float(x.can or 0)
                                    - float(kw["can_leido"] or 0)) < 1e-6
                            and (x.synckey or "") == (
                                kw["synckey_leida"] or "")):
                        self.lineas_incidencia[i] = _replace(
                            x, fecha_int=kw["fecha_int"])
            elif s["sql"] == "insert" and self._cod(
                    kw["horide"]).startswith("CI"):
                o = kw["obra"]
                self.lineas_incidencia.append(LineaIncidenciaSigrid(
                    self.synckeys[kw["synckey"]].ide, kw["reside"],
                    kw["fecha_int"], self._cod(kw["horide"]), kw["synckey"],
                    "PT26/00251" if kw["hmoide"] == 777 else "PT26/00040",
                    can=kw["can"], hmoide=kw["hmoide"], parte_est=1,
                    obride=o.ide, cenide=getattr(o, "cenide", None),
                    paride=kw["paride"], caaide=kw["caaide"], parte_emp=1))
        return n

    def ediciones(self):
        return [(s["parameters"]["ide"], s["parameters"]["fec_leida"],
                 s["parameters"]["fecha_int"],
                 s["parameters"]["can_leido"])
                for s in self.escritos if s["sql"] == "editar_fec"]

    def de_incidencia(self):
        return [(i["hmoide"], i["fecha_int"], self._cod(i["horide"]),
                 i["synckey"]) for i in self.inserts()
                if self._cod(i["horide"]).startswith("CI")]


def _ejr(cli, incs=(), *, lineas=(), contexto=None, pisar=None):
    pipe = RegistroPipeline(cliente=cli, settings=SettingsFalso(
        obra_pruebas_forzar=False), contexto=contexto)
    kw = {"incidencias": list(incs)} if incs else {}
    return pipe.ejecutar(obra=OBRA, lineas=list(lineas), pisar_claves=pisar,
                         **kw)


def _traza(res, i):
    """La traza que guardaría la api de la incidencia `i` (F-030 R39)."""
    por_rol = {a.rol: a for a in res.incidencias if a.id == i}
    out = {}
    for rol in ("ini", "fin"):
        a = por_rol.get(rol)
        if a is not None and a.hmores_ide:
            out[f"hmores_ide_{rol}"] = a.hmores_ide
            out[f"dia_{rol}"] = a.fecha_int % 100
    return out


def test_f062_c1_ejecutar_abre_y_cierra_y_repetir_no_escribe():
    cli = ClienteRachas()
    res = _ejr(cli, [_inc()])
    assert cli.de_incidencia() == [(777, 20261005, "CIV", SK_INI),
                                   (777, 20261009, "CIZ", SK_FIN)]
    assert all(a.hmores_ide for a in res.incidencias)
    antes = len(cli.escritos)
    res = _ejr(cli, [_inc(**_traza(res, 7))])
    assert len(cli.escritos) == antes                          # C9, R18
    assert [a.accion for a in res.incidencias] == ["ya_registrado"] * 2


def test_f062_c2_ejecutar_el_ciz_del_9_al_16_sin_insert():
    cli = ClienteRachas()
    traza = _traza(_ejr(cli, [_inc()]), 7)
    n = len(cli.de_incidencia())
    res = _ejr(cli, [_inc(**traza), _inc(8, 12, 16)])
    assert cli.ediciones() == [(traza["hmores_ide_fin"], 20261009, 20261016,
                                0.0)]
    assert len(cli.de_incidencia()) == n                       # sin INSERT
    assert [(a.id, a.rol, a.accion) for a in res.incidencias] == [
        (7, "ini", "ya_registrado"), (7, "fin", "editar"),
        (8, "ini", "continua"), (8, "fin", "continua")]
    fin = next(x for x in cli.lineas_incidencia
               if x.ide == traza["hmores_ide_fin"])
    assert fin.fecha_int == 20261016
    antes = len(cli.escritos)
    traza = {**traza, "dia_fin": 16}
    _ejr(cli, [_inc(**traza), _inc(8, 12, 16)])
    assert len(cli.escritos) == antes                          # C9


def test_f062_c6_ejecutar_mueve_el_ciz_ajeno_con_su_can_y_lo_devuelve():
    adm = [_l(61, 20261005, obride=40, parte_emp=1),
           _l(62, 20261007, "CIZ", obride=40, parte_emp=1, can=1.0)]
    cli = ClienteRachas(adm)
    res = _ejr(cli, [_inc()], lineas=[linea(registro_id=1, mes=10)])
    assert cli.ediciones() == [(62, 20261007, 20261009, 1.0)]
    assert cli.de_incidencia() == []
    fin = res.incidencias[1]
    assert (fin.accion, fin.ajena, fin.hmores_ide) == ("editar", True, 62)
    # R15: la api guarda el `ide` y el día original; repetir no hace nada.
    traza = {"hmores_ide_fin": 62, "dia_fin": 9, "dia_fin_antes": 7}
    antes = len(cli.escritos)
    res = _ejr(cli, [_inc(**traza)], lineas=[linea(registro_id=1, mes=10)])
    assert [s for s in cli.escritos[antes:]
            if s["sql"] == "editar_fec"] == []
    # C9 (R17): quitarla devuelve el CIZ al 7 y no sale en `no_coincide`.
    res = _ejr(cli, lineas=[linea(registro_id=1, mes=10)],
               contexto=ContextoRachas(quitadas=[_inc(**traza)]))
    assert cli.ediciones()[-1] == (62, 20261009, 20261007, 1.0)
    assert [(a.rol, a.accion) for a in res.incidencias] == [
        ("devolver", "editar")]
    assert [x.fecha_int for x in cli.lineas_incidencia if x.ide == 62] == [
        20261007]
    assert all(62 not in [x.ide for x in n.lineas] for n in res.no_coincide)


def test_f062_r5_ejecutar_el_ciz_va_al_parte_del_inicio_con_su_obra():
    adm = [_l(61, 20261001, obride=40, cenide=4, paride=300, caaide=400,
              parte_emp=1)]
    cli = ClienteRachas(adm)
    res = _ejr(cli, [_inc()])
    [ins] = [i for i in cli.inserts() if i["synckey"] == SK_FIN]
    assert (ins["hmoide"], ins["obra"].ide, ins["obra"].cenide,
            ins["paride"], ins["caaide"], ins["fecha_int"], ins["can"],
            ins["ano"], ins["mes"], ins["horide"], ins["pos"]) == (
        640, 40, 4, 300, 400, 20261009, 0.0, 2026, 10, 79, 128)
    assert not any(s["sql"] == "crear" for s in cli.escritos)
    assert res.incidencias[1].hmores_ide == cli.synckeys[SK_FIN].ide


def test_f062_c4_ejecutar_escribe_el_cierre_del_mes_anterior():
    octubre = [_l(51, 20261027, sk="porcentajes:inc:5:ini", hmoide=777,
                  parte="PT26/00251", obride=555001, cenide=555101,
                  paride=0, caaide=0, parte_emp=1)]
    cli = ClienteRachas(octubre)
    res = _ejr(cli, lineas=[linea(registro_id=1, mes=11)],
               contexto=ContextoRachas(cierres_recursos=[200]))
    [ins] = [i for i in cli.inserts()
             if i["synckey"] == "porcentajes:inc:5:fin"]
    assert (ins["hmoide"], ins["obra"].ide, ins["obra"].cenide,
            ins["fecha_int"], ins["can"], ins["pre"], ins["horide"],
            ins["ano"], ins["mes"], ins["reside"]) == (
        777, 555001, 555101, 20261031, 0.0, 0.0, 79, 2026, 10, 200)
    [c] = res.cierres_racha
    assert c.accion == "escribir" and c.hmores_ide == cli.synckeys[
        "porcentajes:inc:5:fin"].ide
    antes = len(cli.escritos)
    _ejr(cli, lineas=[linea(registro_id=1, mes=11)],
         contexto=ContextoRachas(cierres_recursos=[200]))
    assert [s for s in cli.escritos[antes:] if s["sql"] == "insert"
            and s["parameters"]["synckey"].startswith(
                "porcentajes:inc:")] == []                     # C9


def test_f062_c12_ejecutar_el_cierre_d14_en_el_parte_de_m1():
    sep = [_l(51, 20260915, sk="porcentajes:inc:3:ini", obride=555001,
              cenide=555101, paride=0, caaide=0, parte_emp=1)]
    cli = ClienteRachas(sep)
    res = _ejr(cli, lineas=[linea(registro_id=1, mes=11)],
               contexto=ContextoRachas(cierres_recursos=[200]),
               pisar={"cierre:51"})
    [ins] = [i for i in cli.inserts()
             if i["synckey"] == "porcentajes:inc:3:fin"]
    assert (ins["hmoide"], ins["fecha_int"], ins["ano"], ins["mes"]) == (
        777, 20261031, 2026, 10)
    assert res.cierres_racha[0].hmores_ide == cli.synckeys[
        "porcentajes:inc:3:fin"].ide


def test_f062_r14_ejecutar_si_una_de_la_cadena_no_cumple_no_se_mueve_ninguna():
    cli = ClienteRachas()
    traza = _traza(_ejr(cli, [_inc()]), 7)
    cli.enlazadas_inc.add(traza["hmores_ide_ini"])
    res = _ejr(cli, [_inc(7, 6, 16, **traza)])
    assert cli.ediciones() == []
    assert [(a.rol, a.accion) for a in res.incidencias] == [
        ("ini", "omitir"), ("fin", "omitir")]


def test_f062_r14_ejecutar_ninguna_sentencia_delete():
    """Design §7: el texto REAL de todas las sentencias de `ejecutar` (alta
    de parte, `INSERT` de la petición y de cierre y `UPDATE` de la `fec`)."""
    from infrastructure.sigrid.sigrid_write_client import SigridWriteClient

    from tests.test_f050_propuesta import _cliente_historial

    real, _ = _cliente_historial()

    class Texto(ClienteRachas):
        def stmt_insert_linea(self, **kw):
            st = real.stmt_insert_linea(**kw)
            self.textos.append(st["sql"])
            return super().stmt_insert_linea(**kw)

        def stmt_editar_fecha_incidencia(self, **kw):
            st = real.stmt_editar_fecha_incidencia(**kw)
            self.textos.append(st["sql"])
            return super().stmt_editar_fecha_incidencia(**kw)

        def stmts_crear_parte(self, **kw):
            self.textos += [s["sql"] for s in real.stmts_crear_parte(**kw)]
            return super().stmts_crear_parte(**kw)

    assert isinstance(real, SigridWriteClient)
    adm = [_l(61, 20261005, obride=40, parte_emp=1),
           _l(62, 20261007, "CIZ", obride=40, parte_emp=1, can=1.0)]
    cli = Texto(adm, parte_existe=False)
    cli.textos = []
    _ejr(cli, [_inc()], lineas=[linea(registro_id=1, mes=10)])
    assert len(cli.textos) >= 3
    assert all("DELETE" not in t.upper() for t in cli.textos)
    assert not any("delete" in s["sql"] for s in cli.escritos)


def test_f062_r17_la_peticion_solo_con_quitadas_devuelve_el_ciz_ajeno():
    """La api crea la petición de una obra que solo tiene quitadas (R24):
    su empresa sale de ellas, no se omite entera."""
    traza = {"hmores_ide_fin": 62, "dia_fin": 9, "dia_fin_antes": 7}
    adm = [_l(61, 20261005, obride=40, parte_emp=1),
           _l(62, 20261009, "CIZ", obride=40, parte_emp=1, can=1.0)]
    ctx = ContextoRachas(quitadas=[_inc(**traza)])
    pf = _pf(_cli(adm), [], contexto=ctx)
    assert [(a.rol, a.accion, a.fecha_int) for a in pf.incidencias] == [
        ("devolver", "editar", 20261007)]
    cli = ClienteRachas(adm)
    _ejr(cli, contexto=ctx)
    assert cli.ediciones() == [(62, 20261009, 20261007, 1.0)]


# ============================= script (T18) ============================== #
def _script(monkeypatch, cli, *argv):
    from tests.test_f030_pipeline_incidencias import _script as script_f030

    return script_f030(monkeypatch, cli, *argv)


def test_f062_r24_script_varias_incidencias_son_una_cadena(monkeypatch,
                                                           capsys):
    cli = ClienteRachas()
    argv = ("--ano", "2026", "--mes", "10", "--incidencia", "200:CIV:5:9",
            "--incidencia", "200:CIV:12:16")
    _script(monkeypatch, cli, "ejecutar", "--confirmar", *argv)
    salida = capsys.readouterr().out
    # C2: una racha, CIV el 5 y CIZ el 16; la segunda, de la cadena.
    assert cli.de_incidencia() == [
        (777, 20261005, "CIV", "porcentajes:inc:990101:ini"),
        (777, 20261016, "CIZ", "porcentajes:inc:990101:fin")]
    assert ("RACHA inc=990101 abre · cierra el 20261016 en el parte "
            "PT26/00251") in salida
    assert "RACHA inc=990102 continua desde 20261005 (PT26/00251)" \
        " · cadena de 990101" in salida
    assert "INCIDENCIA inc=990102 ini continua" in salida


def test_f062_r12_script_cierres_sin_incidencias_cierra_el_mes_anterior(
        monkeypatch, capsys):
    octubre = [_l(51, 20261027, sk="porcentajes:inc:990101:ini",
                  hmoide=777, parte="PT26/00251", obride=828942,
                  cenide=828943, paride=0, caaide=0, parte_emp=1)]
    cli = ClienteRachas(octubre)
    argv = ("--ano", "2026", "--mes", "11", "--cierres", "200")
    _script(monkeypatch, cli, "preflight", *argv)
    salida = capsys.readouterr().out
    assert ("CIERRE recurso=200 CIV inicio=51 20261027 (PT26/00251) "
            "escribir fec=20261031 parte=PT26/00251") in salida
    # La línea testigo (0 %, solo da el periodo y la empresa) se omite.
    assert "reg=990201" in salida and "[omitir" in salida
    assert "reg=9000" not in salida                 # sin las de ejemplo
    assert cli.escritos == []
    _script(monkeypatch, cli, "ejecutar", "--confirmar", *argv)
    salida = capsys.readouterr().out
    [cierre] = cli.de_incidencia()
    assert cierre == (777, 20261031, "CIZ", "porcentajes:inc:990101:fin")
    assert [i for i in cli.inserts() if i["synckey"].startswith(
        "porcentajes:99")] == []                    # el testigo, nunca
    assert "CIERRE recurso=200 CIV inicio=51" in salida
    assert "hmores.ide=" in salida.split("CIERRE recurso=200")[-1]


def test_f062_r30_script_imprime_lo_que_no_coincide(monkeypatch, capsys):
    lineas = [_l(91, 20261020, "CIE", obride=828942, parte_emp=1),
              _l(92, 20261022, "CIZ", obride=828942, parte_emp=1)]
    _script(monkeypatch, _cli(lineas), "preflight", "--ano", "2026", "--mes",
            "10", "--cierres", "200")
    salida = capsys.readouterr().out
    assert ("NO COINCIDE solo_sigrid recurso=200 inc=None: "
            "91 CIE 20261020 (PT26/00040); 92 CIZ 20261022 (PT26/00040)"
            ) in salida


def test_f062_r24_script_cierres_mal_escrito(monkeypatch):
    with pytest.raises(SystemExit):
        _script(monkeypatch, ClienteRachas(), "preflight", "--cierres", "x")


def test_f062_r22_la_racha_nueva_lleva_el_parte_donde_se_escribe():
    pf = _pf(_cli(), [_inc(7, 5, 9), _inc(8, 12, 16)])
    assert [(r.id, r.inicio_parte, r.cierre_parte) for r in pf.rachas] == [
        (7, "PT26/00251", "PT26/00251"), (8, "PT26/00251", "PT26/00251")]
    # Con el parte por crear: el que dicen sus líneas, en el preflight y
    # en `ejecutar`.
    pf = _pf(_cli(cls=lambda: ClienteInc(parte_existe=False)), [_inc()])
    parte = pf.incidencias[0].parte_cod
    assert [(r.inicio_parte, r.cierre_parte) for r in pf.rachas] == [
        (parte, parte)]
    res = _ejr(ClienteRachas(parte_existe=False), [_inc()])
    parte = res.incidencias[0].parte_cod
    assert parte is not None
    assert [(r.inicio_parte, r.cierre_parte) for r in res.rachas] == [
        (parte, parte)]


def test_f062_c13_ejecutar_sin_su_clave_el_cierre_d14_queda_pendiente():
    from interface_adapters.api.app import _con_rachas

    sep = [_l(51, 20260915, sk="porcentajes:inc:3:ini", obride=555001,
              cenide=555101, paride=0, caaide=0, parte_emp=1)]
    ctx = ContextoRachas(cierres_recursos=[200])
    testigo = [linea(registro_id=1, mes=11, porcentaje=0.0)]
    pf = _pf(_cli(sep), [], lineas=testigo, contexto=ctx)
    [c] = pf.cierres_racha
    assert (c.accion, c.requiere_confirmar, c.clave) == (
        "escribir", True, "cierre:51")
    [publico] = _con_rachas({}, pf)["cierres_racha"]
    assert (publico["clave"], publico["requiere_confirmar"]) == (
        "cierre:51", True)
    # Sin su clave: ningún INSERT, `pendiente`, ni conflicto ni pendiente de
    # confirmar (no es un pisado de líneas).
    cli = ClienteRachas(sep)
    res = _ejr(cli, lineas=testigo, contexto=ctx, pisar={"1:MENC"})
    assert cli.inserts() == [] and cli.escritos == []
    [c] = res.cierres_racha
    assert (c.accion, c.hmores_ide) == ("pendiente", None)
    assert res.pendientes_confirmacion == []
    # Con ella, se escribe (C12).
    res = _ejr(cli, lineas=testigo, contexto=ctx, pisar={"cierre:51"})
    assert [i["synckey"] for i in cli.inserts()] == ["porcentajes:inc:3:fin"]
    assert res.cierres_racha[0].accion == "escribir"


def test_f062_r31_ejecutar_el_pendiente_dice_su_clave():
    sep = [_l(51, 20260915, sk="porcentajes:inc:3:ini", obride=555001,
              cenide=555101, paride=0, caaide=0, parte_emp=1)]
    res = _ejr(ClienteRachas(sep),
               lineas=[linea(registro_id=1, mes=11, porcentaje=0.0)],
               contexto=ContextoRachas(cierres_recursos=[200]))
    [c] = res.cierres_racha
    assert c.motivo == (
        "la racha CIV del 15/09 (parte PT26/00040) no sigue en 11/2026: CIZ "
        "el 31/10 en el parte PT26/00251; sin confirmar, no se escribe: "
        "marca cierre:51 para cerrarla")


def test_f062_r31_script_el_cierre_pendiente_dice_como_confirmarlo(
        monkeypatch, capsys):
    sep = [_l(51, 20260915, sk="porcentajes:inc:3:ini", hmoide=777,
              parte="PT26/00251", obride=828942, cenide=828943, paride=0,
              caaide=0, parte_emp=1)]
    cli = ClienteRachas(sep)
    argv = ("--ano", "2026", "--mes", "11", "--cierres", "200")
    _script(monkeypatch, cli, "ejecutar", "--confirmar", *argv)
    salida = capsys.readouterr().out
    assert "PENDIENTE cierre:51: relanza con --pisar cierre:51" in salida
    assert cli.de_incidencia() == []
    _script(monkeypatch, cli, "ejecutar", "--confirmar", *argv,
            "--pisar", "cierre:51")
    salida = capsys.readouterr().out
    assert "PENDIENTE cierre:51" not in salida
    assert [x[3] for x in cli.de_incidencia()] == ["porcentajes:inc:3:fin"]
