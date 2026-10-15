# tests/test_f055_propuesta_lote.py
"""F-055 · T8: `POST /api/partidas/propuesta-lote` (R34, R21, R24, R25; C7).

- R34: `{peticiones: [PropuestaIn]}`, mismo `ano`/`mes` o 422 → `{ok,
  obras}`: por petición, en su orden, `{ok: true, propuestas}` (las de
  `POST /api/partidas/propuesta`) o `{ok: false, error}`. Obras e
  historial, UNA lectura por lote; presupuestos, uno por obra en paralelo.
- R21: cada petición da las mismas `propuestas` suelta y en lote: se prueba
  repitiendo en lote cada propuesta de `test_f050_endpoint_propuesta` y de
  `test_f055_orden_propuesta` (plugin `tests/f055_equivalencia_lote.py`).
- R24: empresa no válida u obra de otra empresa, solo su entrada; fallo del
  historial (compartido), 502. R25: ruta síncrona.
- C7: 10 obras: 1 lectura de obras, 1 de historial y 10 de presupuesto, en
  ≤ 4 rondas con límite 4.

Sin red ni BBDD. Los `ide` son inventados.
"""
from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
from types import SimpleNamespace

import pytest
from application.pipelines.registro_lote import RegistroLote
from domain.models.registro_models import ObraEntrada
from fastapi.testclient import TestClient
from interface_adapters.api import app as modulo_app

from tests.conftest import _fila
from tests.test_f050_endpoint_propuesta import AJUSTES
from tests.test_f050_pipeline import _h
from tests.test_f055_lecturas_lote import contar_tandas
from tests.test_f055_lote import SERVICIO, ClienteObras, _ajustes

RUTA = "/api/partidas/propuesta-lote"
ESCENARIOS = ["tests/test_f050_endpoint_propuesta.py",
              "tests/test_f055_orden_propuesta.py"]


class ClientePresupuestos(ClienteObras):
    """`ClienteObras` con el presupuesto de cada obra (`capitulos_de_obra`):
    la obra `600000 + i` tiene la hoja `CI.1.9` (ADMINISTRATIVO) de `ide`
    `700000 + i` y la `CI.1.10` (ENCARGADO (ACUNA)) de `ide` `710000 + i`."""

    def __init__(self, n=10, historial=(), **kw) -> None:
        super().__init__(n, historial=historial, **kw)

    def capitulos_de_obra(self, obride):
        i = int(obride) - 600000
        if not 1 <= i <= len(self.obras):
            return []
        return [_fila(690000 + i, 0, 0, "CI", "COSTES INDIRECTOS"),
                _fila(700000 + i, 690000 + i, 1, "CI.1.9", "ADMINISTRATIVO"),
                _fila(710000 + i, 690000 + i, 2, "CI.1.10",
                      "ENCARGADO (ACUNA)")]


def _linea(clave="a", recurso=200, categoria="Encargado",
           nombre="Acuna Mera, Antonio", pv=False) -> dict:
    return {"clave": clave, "recurso_ide": recurso, "categoria": categoria,
            "nombre": nombre, "es_postventa": pv}


def _peticion(i, *lineas, empresa=1, ano=2026, mes=7) -> dict:
    return {"empresa": empresa, "obra": ObraEntrada(ide=600000 + i),
            "ano": ano, "mes": mes, "lineas": list(lineas) or [_linea()]}


def _proponer(cli, peticiones, limite=4):
    return RegistroLote(cliente=cli, settings=_ajustes(),
                        limite=limite).proponer(peticiones)


# ================== R21 · los escenarios de hoy, en lote ================== #
def test_f055_r21_cada_propuesta_da_lo_mismo_suelta_y_en_lote(tmp_path):
    salida = tmp_path / "cuenta.json"
    r = subprocess.run(
        [sys.executable, "-m", "pytest", *ESCENARIOS, "-q", "-x",
         "-p", "no:cacheprovider", "-p", "tests.f055_equivalencia_lote"],
        cwd=SERVICIO, capture_output=True, text=True, timeout=300,
        env={**os.environ, "F055_EQUIVALENCIA_SALIDA": str(salida)})
    assert r.returncode == 0, r.stdout[-3000:] + r.stderr[-2000:]
    cuenta = json.loads(salida.read_text(encoding="utf-8"))
    assert cuenta["propuestas_iguales"] >= 11, cuenta
    assert cuenta["propuestas_error_iguales"] >= 2, cuenta


# ======================= R34 · forma y una lectura ======================== #
def test_f055_r34_propuestas_por_obra_y_en_su_orden():
    hist = [_h(recurso=200, obra=600002, paride=700002, cod="CI.1.9")]
    cli = ClientePresupuestos(3, historial=hist)
    r = _proponer(cli, [_peticion(2), _peticion(1, _linea("x", 400, "X",
                                                           "Nadie"))])
    assert r[0] == {"ok": True, "propuestas": {"a": {
        "paride": 700002, "cod": "CI.1.9", "res": "ADMINISTRATIVO",
        "metodo": "parte_anterior",
        "origen": "parte PT26/00100 · 07/2026 · obra 0678"}}}
    assert r[1] == {"ok": True, "propuestas": {"x": None}}


def test_f055_r34_las_mismas_propuestas_que_el_selector_suelto():
    from application.pipelines.registro_pipeline import RegistroPipeline
    hist = [_h(recurso=200, obra=600001, paride=700001, cod="CI.1.9"),
            _h(recurso=400, obra=600009, paride=999, cod="CI.1.10",
               res="ENCARGADO (ACUNA)")]
    peticiones = [_peticion(i, _linea("a"), _linea("b", 400, "X", "Nadie"))
                  for i in (1, 2)]
    lote = _proponer(ClientePresupuestos(2, historial=hist), peticiones)
    for p, r in zip(peticiones, lote):
        suelto = RegistroPipeline(
            cliente=ClientePresupuestos(2, historial=hist),
            settings=_ajustes()).proponer(**p)
        assert r == {"ok": True, "propuestas": suelto["propuestas"]}


def test_f055_r34_obras_e_historial_una_vez_presupuesto_por_obra():
    cli = ClientePresupuestos(3)
    _proponer(cli, [_peticion(i, _linea("a"), _linea("b", 400))
                    for i in (1, 2, 3)])
    n = cli.nombres()
    assert n.count("obras_por_ide") == 1
    assert n.count("historial_partidas") == 1
    assert ("historial_partidas", [200, 400], 202407, 202607) in cli.llamadas
    assert sorted(c[1] for c in cli.llamadas
                  if c[0] == "capitulos_de_obra") == [600001, 600002, 600003]
    assert sorted(set(n)) == ["capitulos_de_obra", "historial_partidas",
                              "obras_por_ide"]


def test_f055_r34_sin_lineas_normales_no_lee_historial():
    cli = ClientePresupuestos(1)
    r = _proponer(cli, [_peticion(1, _linea("pv", pv=True))])
    assert "historial_partidas" not in cli.nombres()
    assert r[0]["ok"] is True


def test_f055_r24_obra_de_otra_empresa_solo_su_entrada():
    cli = ClientePresupuestos(2)
    cli.obras[600002].empresa = 28
    r = _proponer(cli, [_peticion(1), _peticion(2), _peticion(9)])
    assert r[0]["ok"] is True
    from application.services.reglas_porcentajes import MOTIVO_EMPRESA_OBRA
    assert r[1] == {"ok": False, "error": MOTIVO_EMPRESA_OBRA.format(
        cod="O002", emp_obra=28, emp_linea=1)}
    assert isinstance(r[2], RuntimeError) and "no encontrada" in str(r[2])


def test_f055_r24_fallo_del_historial_hace_fallar_el_lote():
    cli = ClientePresupuestos(2)

    def falla(*a):
        raise RuntimeError("sigrid-api devolvio una respuesta truncada")

    cli.historial_partidas = falla
    with pytest.raises(RuntimeError, match="truncada"):
        _proponer(cli, [_peticion(1), _peticion(2)])


# ================================== C7 =================================== #
def test_f055_c7_diez_obras_1_obras_1_historial_10_presupuestos(
        monkeypatch):
    """Rondas por estructura: A (obras e historial) una tanda; B (10
    presupuestos con límite 4) tres; ninguna lectura después."""
    tandas = contar_tandas(monkeypatch)
    cli = ClientePresupuestos(espera=0.01)
    r = _proponer(cli, [_peticion(i) for i in range(1, 11)], limite=4)
    assert all(x["ok"] for x in r)
    n = cli.nombres()
    assert (n.count("obras_por_ide"), n.count("historial_partidas"),
            n.count("capitulos_de_obra"), len(n)) == (1, 1, 10, 12)
    assert tandas == [(2, 1), (10, 3)]
    assert sum(t for _, t in tandas) <= 4
    assert cli.max_a_la_vez <= 4


# ================================= HTTP =================================== #
@pytest.fixture
def api(monkeypatch):
    def fabricar(cli):
        monkeypatch.setattr(modulo_app, "SigridWriteClient",
                            lambda **kw: cli)
        return TestClient(modulo_app.build_app(SimpleNamespace(
            **{**AJUSTES, "sigrid_lecturas_paralelas": 4})))
    return fabricar


def _json(i, *, empresa=1, ano=2026, mes=7, lineas=None) -> dict:
    return {"empresa": empresa, "obra": {"ide": 600000 + i}, "ano": ano,
            "mes": mes, "lineas": lineas or [_linea()]}


def test_f055_r34_ruta_forma_y_errores_por_entrada(api):
    cli = ClientePresupuestos(2)
    cli.obras[600002].empresa = 28
    r = api(cli).post(RUTA, json={"peticiones": [
        _json(1), _json(2), _json(3, empresa=None), _json(9)]})
    assert r.status_code == 200, r.text
    obras = r.json()["obras"]
    assert r.json()["ok"] is True and len(obras) == 4
    assert obras[0] == {"ok": True, "propuestas": {"a": {
        "paride": 710001, "cod": "CI.1.10", "res": "ENCARGADO (ACUNA)",
        "metodo": "auto_nombre", "origen": None}}}
    assert obras[1]["ok"] is False and "28" in obras[1]["error"]
    assert obras[2] == {"ok": False, "error": "empresa no válida: None"}
    assert obras[3] == {"ok": False, "error": (
        "obra no encontrada en Sigrid (ide=600009 cod=None empresa=1)")}


def test_f055_r34_ruta_mismas_que_el_selector(api):
    cli = ClientePresupuestos(1)
    suelto = api(ClientePresupuestos(1)).post(
        "/api/partidas/propuesta", json=_json(1)).json()
    lote = api(cli).post(RUTA, json={"peticiones": [_json(1)]}).json()
    assert lote["obras"][0]["propuestas"] == suelto["propuestas"]


@pytest.mark.parametrize("otra", [{"ano": 2025}, {"mes": 8}])
def test_f055_r34_ano_o_mes_distintos_422(api, otra):
    r = api(ClientePresupuestos(2)).post(RUTA, json={"peticiones": [
        _json(1), _json(2, **otra)]})
    assert r.status_code == 422
    assert r.json()["ok"] is False and "mismo" in r.json()["error"]


def test_f055_r34_ruta_sin_peticiones(api):
    r = api(ClientePresupuestos(1)).post(RUTA, json={"peticiones": []})
    assert r.json() == {"ok": True, "obras": []}


def test_f055_r24_ruta_fallo_compartido_502(api):
    cli = ClientePresupuestos(1)

    def falla(*a):
        raise RuntimeError("sigrid-api caída")

    cli.historial_partidas = falla
    r = api(cli).post(RUTA, json={"peticiones": [_json(1)]})
    assert r.status_code == 502
    assert r.json() == {"ok": False, "error": "sigrid-api caída"}


def test_f055_r25_la_ruta_es_sincrona():
    app = modulo_app.build_app(SimpleNamespace(**AJUSTES))
    [ruta] = [r for r in app.routes if getattr(r, "path", "") == RUTA]
    assert not inspect.iscoroutinefunction(ruta.endpoint)
