# tests/test_f062_punta_a_punta.py
"""F-062 · las rachas de punta a punta, mitad del transfer (design §3, como
F-030 §13.6).

Cada paso de `tests/contratos/f062_rachas.json` trae la petición que la api
TIENE que mandar (lo comprueba la otra mitad,
`services/dedicacion-api/tests/test_f062_punta_a_punta.py`) y lo que hay en
Sigrid antes. Aquí se ejecuta por HTTP (`app.py` y el `RegistroPipeline`
reales) contra el Sigrid falso de las rachas (`ClienteRachas`): la respuesta
tiene que ser la del contrato (la que la api traza) y lo escrito, solo sus
`ediciones` e `inserciones`, sin ningún `DELETE` (R14). Ni red ni BBDD.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_f050_endpoint_propuesta import AJUSTES
from tests.test_f062_pipeline_rachas import ClienteRachas, _l

CONTRATO = json.loads(
    (Path(__file__).resolve().parents[3] / "tests" / "contratos"
     / "f062_rachas.json").read_text(encoding="utf-8"))
PASOS = [(f"{e['nombre']}-{p['nombre']}", p)
         for e in CONTRATO["escenarios"] for p in e["pasos"]]
#: Las claves de cada línea de incidencia de la respuesta que fija el
#: contrato (`fec_antes` solo en `editar`; `ajena`, solo si lo es).
CLAVES = ("id", "rol", "accion", "fecha_int", "parte_cod", "hmores_ide")


def _sigrid(lineas: list[dict]) -> list:
    return [_l(x["ide"], x["fecha_int"], x["codigo"], sk=x["synckey"],
               parte=x["parte_cod"], hmoide=x["hmoide"], can=x["can"],
               obride=x["obride"], cenide=x["obride"] + 100, paride=0,
               caaide=0, parte_emp=1)
            for x in lineas]


def _incidencia(x: dict, esperada: dict) -> dict:
    """La de la respuesta con las claves del contrato; en una `escribir`,
    el `hmores_ide` es el que dio el Sigrid falso (cualquiera, no nulo)."""
    out = {k: x[k] for k in CLAVES}
    out.update({k: x[k] for k in ("fec_antes", "ajena") if k in x})
    if x["accion"] == "escribir":
        assert x["hmores_ide"] is not None
        out["hmores_ide"] = esperada.get("hmores_ide")
    return out


@pytest.mark.parametrize("paso", [p for _, p in PASOS],
                         ids=[n for n, _ in PASOS])
def test_f062_punta_a_punta_el_transfer_hace_lo_del_contrato(monkeypatch,
                                                             paso):
    from fastapi.testclient import TestClient
    from interface_adapters.api import app as modulo_app

    cli = ClienteRachas(_sigrid(paso["sigrid"]))
    monkeypatch.setattr(modulo_app, "SigridWriteClient", lambda **kw: cli)
    http = TestClient(modulo_app.build_app(SimpleNamespace(**{
        **AJUSTES, "obra_pruebas_forzar": False,
        "incidencias_meses_atras": 12})))
    r = http.post("/api/registro/ejecutar", json=paso["peticion"])
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    esperada = paso["respuesta"]
    incs = esperada.get("incidencias", [])
    assert [_incidencia(x, e) for x, e in zip(
        cuerpo.get("incidencias", []), incs)] == incs
    assert len(cuerpo.get("incidencias", [])) == len(incs)
    assert cuerpo["cierres_racha"] == esperada["cierres_racha"]
    assert cuerpo["no_coincide"] == esperada["no_coincide"]
    # Lo escrito: solo esas ediciones e inserciones; ningún DELETE.
    assert [[ide, antes, nueva] for ide, antes, nueva, _ in cli.ediciones()
            ] == paso["ediciones"]
    assert [[fec, cod] for _, fec, cod, _ in cli.de_incidencia()] \
        == paso["inserciones"]
    assert not [s for s in cli.escritos
                if "DELETE" in str(s.get("sql", "")).upper()]
