# tests/test_f054_rutas.py
"""F-054 · T5 y T8: el cliente del transfer para traer de Sigrid y la ruta
`POST /api/v1/periodos/{anio}/{mes}/traer-sigrid` (R2, R3, R26, R27).

T5 (`-k cliente`): `TransferClient.porcentajes_existentes` manda `{empresa,
ano, mes, obras}` a `POST /api/porcentajes/existentes` y devuelve un
`ResultadoExistentes`; `ok` que no es `true`, sin `lineas` o un error HTTP
⇒ `PorcentajesSigridNoDisponible` con el motivo (502 en la api).

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
