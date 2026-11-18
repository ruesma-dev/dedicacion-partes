# tests/test_f054_endpoint.py
"""F-054 · T3: `POST /api/porcentajes/existentes` (R3, R7; contrato de
design §1).

- Contrato: `{empresa, ano, mes, obras}` → `{ok, lineas_leidas,
  excluidas_pruebas, obra_postventa, motivo_postventa, obra_var,
  motivo_var, lineas}`; cada línea con lo de R6 y su entrada.
- Empresa no válida ⇒ 422 sin leer nada.
- R3: una lectura que falla o viene truncada ⇒ 502 con el motivo.
- R7: nunca escribe en Sigrid, con `OBRA_PRUEBAS_FORZAR` a true y a false.

`TestClient` sobre la app real con el cliente de Sigrid sustituido por el
doble de `test_f054_traduccion.py`, que revienta si se escribe.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from interface_adapters.api import app as modulo_app

from tests.conftest import OBRA_POSTVENTA, OBRA_PRUEBAS
from tests.test_f039_universo_var import OBRA_VAR, VAR_IDE
from tests.test_f050_endpoint_propuesta import AJUSTES
from tests.test_f054_traduccion import (
    P29,
    PV_IDE,
    ClienteExistentes,
    _l,
)

RUTA = "/api/porcentajes/existentes"


class ClienteQueNoEscribe(ClienteExistentes):
    def escribir(self, statements):
        raise AssertionError("traer de Sigrid no escribe")


def _api(monkeypatch, cli, **ajustes):
    monkeypatch.setattr(modulo_app, "SigridWriteClient", lambda **kw: cli)
    return TestClient(modulo_app.build_app(SimpleNamespace(
        **{**AJUSTES, **ajustes})))


def _peticion(**kw) -> dict:
    return {"empresa": 1, "ano": 2026, "mes": 9,
            "obras": [{"ide": 555001, "codigo": "0678",
                       "nombre": "15 VIVIENDAS"}], **kw}


LINEAS = [_l(1, 828942, OBRA_PRUEBAS), _l(2, 694, "0694", paride=2105),
          _l(3, PV_IDE, OBRA_POSTVENTA, paride=70001),
          _l(4, VAR_IDE, OBRA_VAR, paride=P29)]


def test_f054_contrato_de_la_respuesta(monkeypatch):
    cli = ClienteQueNoEscribe(LINEAS)
    r = _api(monkeypatch, cli).post(RUTA, json=_peticion())
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert set(cuerpo) == {"ok", "lineas_leidas", "excluidas_pruebas",
                           "obra_postventa", "motivo_postventa", "obra_var",
                           "motivo_var", "lineas",
                           "vinculados_registrados"}  # F-069 (R31)
    assert cuerpo["ok"] is True
    assert (cuerpo["lineas_leidas"], cuerpo["excluidas_pruebas"]) == (4, 1)
    assert [(x["hmores_ide"], x["destino"], x["obra_origen_ide"],
             x["var_paride"], x["motivo"]) for x in cuerpo["lineas"]] == [
        (2, "normal", None, None, None),
        (3, "postventa", 555001, None, None),
        (4, "var", None, P29, None)]
    assert set(cuerpo["lineas"][0]) == {
        "hmores_ide", "recurso_ide", "obra_ide", "obra_cod", "parte_ide",
        "parte_cod", "parte_est", "en_registro", "hora", "can", "fec",
        "paride", "partida_cod", "partida_res", "synckey", "tex",
        "destino", "obra_origen_ide", "var_paride", "motivo"}
    assert cuerpo["obra_postventa"]["ide"] == PV_IDE
    assert cuerpo["obra_var"]["ide"] == VAR_IDE
    assert cli.leidas_mensuales == [(1, 2026, 9, None, True)]


def test_f054_las_obras_de_la_peticion_son_las_del_casado(monkeypatch):
    cli = ClienteQueNoEscribe([_l(3, PV_IDE, OBRA_POSTVENTA, paride=70001)])
    r = _api(monkeypatch, cli).post(RUTA, json=_peticion(obras=[]))
    assert r.json()["lineas"][0]["obra_origen_ide"] is None


@pytest.mark.parametrize("empresa", [None, 0, -1, True, "x"])
def test_f054_empresa_no_valida_422_sin_leer(monkeypatch, empresa):
    cli = ClienteQueNoEscribe(LINEAS)
    cuerpo = _peticion()
    cuerpo["empresa"] = empresa
    if empresa is None:
        del cuerpo["empresa"]
    r = _api(monkeypatch, cli).post(RUTA, json=cuerpo)
    assert r.status_code == 422
    assert r.json()["ok"] is False
    assert cli.leidas_mensuales == []


def test_f054_r3_lectura_que_falla_502(monkeypatch):
    class Falla(ClienteQueNoEscribe):
        def lineas_mensuales_del_periodo(self, *a, **k):
            raise RuntimeError("sigrid-api devolvio una respuesta truncada")

    r = _api(monkeypatch, Falla()).post(RUTA, json=_peticion())
    assert r.status_code == 502
    assert r.json() == {"ok": False,
                        "error": "sigrid-api devolvio una respuesta truncada"}


def test_f054_r3_catalogo_que_falla_502(monkeypatch):
    class Falla(ClienteQueNoEscribe):
        def capitulos_de_obra(self, obride):
            raise RuntimeError("sigrid-api read HTTP 500")

    r = _api(monkeypatch, Falla(LINEAS)).post(RUTA, json=_peticion())
    assert r.status_code == 502 and "HTTP 500" in r.json()["error"]


@pytest.mark.parametrize("forzar", [True, False])
def test_f054_r7_nunca_escribe(monkeypatch, forzar):
    cli = ClienteQueNoEscribe(LINEAS)
    r = _api(monkeypatch, cli, obra_pruebas_forzar=forzar).post(
        RUTA, json=_peticion())
    assert r.status_code == 200, r.text
    assert cli.escritos == []
    # El modo pruebas no cambia lo que se lee ni lo que se traduce (R5).
    assert r.json()["excluidas_pruebas"] == 1
