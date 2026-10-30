# tests/test_f054_rutas.py
"""F-054 · T5 y T8: el cliente del transfer para traer de Sigrid y la ruta
`POST /api/v1/periodos/{anio}/{mes}/traer-sigrid` (R2, R3, R26, R27).

T5 (`-k cliente`): `TransferClient.porcentajes_existentes` manda `{empresa,
ano, mes, obras}` a `POST /api/porcentajes/existentes` y devuelve un
`ResultadoExistentes`; `ok` que no es `true`, sin `lineas` o un error HTTP
⇒ `PorcentajesSigridNoDisponible` con el motivo (502 en la api).

T8 (el resto): la ruta con la app real. Sin `aceptar` (o sin cuerpo)
compara; con él, escribe con el `X-Usuario` y encola las propuestas solo de
los tocados (R26); la salida de R27 (con `de_vinculados`); la empresa
elegida filtra trabajadores y no las obras; 404/409 sin llamar al
transfer (R2), 502 con motivo (R3) y 422 de cuerpo o empresa.

Sin red ni BBDD.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from domain.errors import PorcentajesSigridNoDisponible
from domain.models import LineaSigridTraida, ResultadoExistentes, TipoEvento
from interface_adapters.api.app import _HTTP_POR_ERROR

LINEA = {"hmores_ide": 9001, "recurso_ide": 4321, "obra_ide": 694,
         "obra_cod": "0694", "parte_ide": 777, "parte_cod": "PT26/00319",
         "parte_est": 1, "en_registro": True, "hora": "MADM", "can": 0.95,
         "fec": 20260930, "paride": 2105, "partida_cod": "CI.1.5",
         "partida_res": "JEFE DE OBRA", "synckey": None, "destino": "normal",
         "obra_origen_ide": None, "var_paride": None, "motivo": None}
RESPUESTA = {"ok": True, "lineas_leidas": 3, "excluidas_pruebas": 1,
             "obra_postventa": None, "motivo_postventa": "pv off",
             "obra_var": None, "motivo_var": None, "lineas": [LINEA]}


def _cliente(monkeypatch, respuesta=None, status=200, excepcion=None):
    import httpx
    from infrastructure.transfer import transfer_client as mod
    llamadas = []

    def post(url, json, timeout):
        llamadas.append((url, json, timeout))
        if excepcion:
            raise excepcion
        return SimpleNamespace(status_code=status, text=str(respuesta),
                               json=lambda: respuesta)

    monkeypatch.setattr(mod.httpx, "post", post)
    _ = httpx
    cli = mod.TransferClient(SimpleNamespace(
        transfer_base_url="http://transfer.invalid/", transfer_timeout_s=7.0))
    return cli, llamadas


def test_f054_cliente_cuerpo_enviado_y_resultado(monkeypatch):
    cli, llamadas = _cliente(monkeypatch, RESPUESTA)
    obras = [{"ide": 678, "codigo": "0678", "nombre": "15 VIVIENDAS"}]
    r = cli.porcentajes_existentes(1, 2026, 9, obras)
    assert llamadas == [("http://transfer.invalid/api/porcentajes/existentes",
                         {"empresa": 1, "ano": 2026, "mes": 9,
                          "obras": obras}, 7.0)]
    assert r == ResultadoExistentes(
        lineas_leidas=3, excluidas_pruebas=1, motivo_postventa="pv off",
        motivo_var=None, lineas=(LineaSigridTraida(**LINEA),))


def test_f054_cliente_claves_de_mas_en_la_linea_se_ignoran(monkeypatch):
    cli, _ = _cliente(monkeypatch, {**RESPUESTA, "lineas": [
        {**LINEA, "nueva": 1}]})
    assert cli.porcentajes_existentes(1, 2026, 9, []).lineas[0].hmores_ide \
        == 9001


@pytest.mark.parametrize("respuesta, status, motivo", [
    ({"ok": False, "error": "sigrid-api devolvio una respuesta truncada"},
     502, "truncada"),
    ({"ok": True}, 200, "no trae líneas"),
    ({"ok": "true", "lineas": []}, 200, "no trae líneas"),
    ({"detail": "x"}, 404, "HTTP 404"),
])
def test_f054_cliente_sin_ok_o_error_http_es_el_error(monkeypatch, respuesta,
                                                      status, motivo):
    cli, _ = _cliente(monkeypatch, respuesta, status)
    with pytest.raises(PorcentajesSigridNoDisponible, match=motivo):
        cli.porcentajes_existentes(1, 2026, 9, [])


def test_f054_cliente_transfer_inaccesible(monkeypatch):
    import httpx
    cli, _ = _cliente(monkeypatch, excepcion=httpx.ConnectError("caido"))
    with pytest.raises(PorcentajesSigridNoDisponible, match="inaccesible"):
        cli.porcentajes_existentes(1, 2026, 9, [])


def test_f054_cliente_el_error_es_502_y_hay_evento_sigrid():
    assert dict(_HTTP_POR_ERROR)[PorcentajesSigridNoDisponible] == 502
    assert TipoEvento.SIGRID.value == "SIGRID"


# ======================= T8 · la ruta traer-sigrid ======================= #
# `TestClient` sobre la app real con el contenedor sustituido: la UoW en
# memoria con transacción de `test_f054_aceptar.py`, el caso de uso con un
# transfer falso y las propuestas falsas de F-055.
from application.traer_sigrid import TraerDeSigrid  # noqa: E402
from config.settings import Settings  # noqa: E402
from domain.models import EstadoPeriodo  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from interface_adapters.api.app import build_app  # noqa: E402
from interface_adapters.api.deps import obtener_contenedor  # noqa: E402

from tests.test_f024_rutas_empresa import _PropuestasFalsas  # noqa: E402
from tests.test_f054_aceptar import (  # noqa: E402
    SIGRID,
    _datos,
    _Gateway,
    _s,
    _Uow,
)

RUTA = "/api/v1/periodos/2026/9/traer-sigrid"


def _app(monkeypatch, datos=None, gateway=None, propuestas=None):
    monkeypatch.delenv("EMPRESA_IMPUTACION", raising=False)
    settings = Settings(_env_file=None)
    datos = datos or _datos()
    gateway = gateway or _Gateway(SIGRID)
    propuestas = propuestas or _PropuestasFalsas()
    contenedor = SimpleNamespace(
        settings=settings, uow=lambda: _Uow(datos),
        propuestas_mes=propuestas, traer_sigrid=TraerDeSigrid(gateway))
    app = build_app(settings)
    app.dependency_overrides[obtener_contenedor] = lambda: contenedor
    return TestClient(app), datos, gateway, propuestas


def test_f054_r27_ruta_sin_aceptar_compara(monkeypatch):
    g = _Gateway([*SIGRID, _s(970, 5000, 694, 1.0, hora="MESVE"),
                  _s(971, 8888, 694, 1.0), _s(972, 30, 694, 0.5)])
    cli, datos, _, prop = _app(monkeypatch, gateway=g)
    r = cli.post(RUTA, json={"aceptar": []})
    assert r.status_code == 200, r.text
    j = r.json()
    assert {k: j[k] for k in ("aceptadas", "rechazadas", "fuera_maestro",
                              "de_vinculados", "lineas_leidas",
                              "excluidas_pruebas", "motivo_postventa",
                              "motivo_var", "propuestas_en_curso")} == {
        "aceptadas": 0, "rechazadas": [], "fuera_maestro": 1,
        "de_vinculados": 1, "lineas_leidas": 7, "excluidas_pruebas": 1,
        "motivo_postventa": "pv", "motivo_var": None,
        "propuestas_en_curso": False}
    assert j["no_traidas"] == [{
        "hmores_ide": 972, "recurso_ide": 30, "obra_cod": "0694",
        "parte_cod": "PT26/972", "can": 0.5,
        "motivo": "el trabajador no está vigente en 09/2026"}]
    ana, bea = j["trabajadores"]
    assert (ana["trabajador_ide"], ana["cod"], ana["nombre"],
            ana["aceptadas"]) == (10, "10", "Ana", [])
    assert ana["entradas"][1] == {
        "obra_ide": 694, "cod": "0694", "descripcion": "OBRA 694",
        "es_postventa": False, "estado": "distinta", "pct_sigrid": 95.0,
        "pct_cuadrante": 60.0, "partida_cod": "CI.1.5",
        "partida_res": "JEFE", "parte_cod": "PT26/901", "n_lineas": 1,
        "motivo": None}
    assert [(e["obra_ide"], e["estado"]) for e in ana["entradas"]] == [
        (678, "solo_cuadrante"), (694, "distinta"), (713, "solo_sigrid")]
    assert ana["entradas"][0]["pct_sigrid"] is None
    assert bea["entradas"][0]["estado"] == "solo_sigrid"
    assert prop.lanzadas == [] and datos.eventos == []


def test_f054_r27_ruta_sin_cuerpo_es_comparar(monkeypatch):
    cli, datos, _, _ = _app(monkeypatch)
    r = cli.post(RUTA)
    assert r.status_code == 200 and r.json()["aceptadas"] == 0
    assert datos.eventos == []


def test_f054_r26_ruta_aceptar_usuario_y_propuestas_de_los_tocados(
        monkeypatch):
    cli, datos, _, prop = _app(monkeypatch,
                               propuestas=_PropuestasFalsas(en_curso=True))
    r = cli.post(RUTA, headers={"X-Usuario": "bea@ruesma.es"}, json={
        "aceptar": [{"trabajador_ide": 20, "obra_ide": 694},
                    {"trabajador_ide": 10, "obra_ide": 678,
                     "es_postventa": False}]})
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["aceptadas"] == 1 and j["propuestas_en_curso"] is True
    assert j["rechazadas"] == [{
        "trabajador_ide": 10, "obra_ide": 678, "es_postventa": False,
        "motivo": "solo está en el cuadrante: la escribe el registro"}]
    assert j["trabajadores"][1]["aceptadas"] == [
        {"obra_ide": 694, "es_postventa": False}]
    assert prop.lanzadas == [(2026, 9, [20])]
    assert [(e[0], e[3]) for e in datos.eventos] == [(20, "bea@ruesma.es")]


def test_f054_ruta_la_empresa_elegida_filtra_trabajadores(monkeypatch):
    g = _Gateway([_s(961, 40, 694, 1.0)])
    cli, _, _, _ = _app(monkeypatch, gateway=g)
    sin = cli.post(RUTA, json={}).json()
    con = cli.post(RUTA + "?empresa=28", json={}).json()
    assert sin["trabajadores"] == [] and len(sin["no_traidas"]) == 1
    assert [t["trabajador_ide"] for t in con["trabajadores"]] == [40]
    assert con["no_traidas"] == []
    # La empresa de las obras no cambia con la elegida.
    assert [c[0] for c in g.llamadas] == [1, 1]


def test_f054_r2_ruta_404_y_409_sin_llamar_al_transfer(monkeypatch):
    cli, datos, g, _ = _app(monkeypatch)
    r = cli.post("/api/v1/periodos/2026/8/traer-sigrid", json={})
    assert r.status_code == 404 and "no existe" in r.json()["error"]
    datos.estado = EstadoPeriodo.CERRADO
    r = cli.post(RUTA, json={})
    assert r.status_code == 409 and "cerrado" in r.json()["error"]
    assert g.llamadas == []


def test_f054_r3_ruta_502_con_motivo_y_sin_propuestas(monkeypatch):
    cli, datos, _, prop = _app(monkeypatch, gateway=_Gateway(
        fallo=PorcentajesSigridNoDisponible(
            "las líneas de Sigrid no están disponibles: truncada")))
    r = cli.post(RUTA, json={"aceptar": [
        {"trabajador_ide": 20, "obra_ide": 694}]})
    assert r.status_code == 502
    assert r.json() == {
        "error": "las líneas de Sigrid no están disponibles: truncada"}
    assert prop.lanzadas == [] and 20 not in datos.filas


@pytest.mark.parametrize("url, cuerpo", [
    (RUTA, {"aceptar": [{"trabajador_ide": 20}]}),
    (RUTA, {"aceptar": [{"trabajador_ide": "x", "obra_ide": 694}]}),
    (RUTA, {"aceptar": [{"trabajador_ide": 20, "obra_ide": 694,
                         "porcentaje": 50}]}),
    (RUTA, {"aceptar": {"trabajador_ide": 20, "obra_ide": 694}}),
    (RUTA, {"otra": 1}),
    (RUTA + "?empresa=0", {}),
    (RUTA + "?empresa=x", {}),
])
def test_f054_ruta_422_sin_llamar_al_transfer(monkeypatch, url, cuerpo):
    cli, datos, g, _ = _app(monkeypatch)
    r = cli.post(url, json=cuerpo)
    assert r.status_code == 422
    assert g.llamadas == [] and datos.eventos == []


def test_f054_ruta_el_contenedor_real_lleva_el_caso_de_uso(monkeypatch):
    from interface_adapters.api import deps
    monkeypatch.delenv("EMPRESA_IMPUTACION", raising=False)
    c = deps.construir_contenedor(Settings(_env_file=None), None)
    assert isinstance(c.traer_sigrid, TraerDeSigrid)
    assert c.traer_sigrid._gateway is c.registro_sigrid._transfer
