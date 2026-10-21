# tests/test_f030_r30_editar.py
"""F-030 · Anexo R30 en el transfer: cambiar los días de una incidencia ya
registrada EDITA la `fec` de sus líneas (R40-R46,
ARCHITECTURE.md#regla-incidencia).

- Contrato (T27): la incidencia trae la traza de la api (`hmores_ide_*`,
  `dia_*`, opcionales) y la acción `editar` publica `fec_antes`.
- Cliente (T28): la lectura de R33 trae `can`, parte y estado y busca
  también por `ide`; el `UPDATE` de la `fec` lleva la guarda de F-051.
- Reglas (T29): `reconciliar`, pura.
- Preflight, lote (T30) y `ejecutar` (T31).

Sin red ni BBDD: el cliente con su `_read` sustituido por un doble y el
pipeline con los dobles de `conftest.py`. Los `ide` son inventados.
"""
from __future__ import annotations

import pytest
from domain.models.registro_models import (
    AccionIncidencia,
    IncidenciaEntrada,
    LineaIncidenciaSigrid,
)

from tests.conftest import OBRA_ORIGEN
from tests.test_f030_pipeline_incidencias import (
    CLAVES_INC,
    ClienteInc,
    _json_inc,
    _json_linea,
)

TRAZA = {"hmores_ide_ini": 9001, "hmores_ide_fin": 9002, "dia_ini": 5,
         "dia_fin": 9}


@pytest.fixture
def api(monkeypatch):
    """La app real con el cliente que se le dé (como la de
    `test_f030_pipeline_incidencias`)."""
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from interface_adapters.api import app as modulo_app

    from tests.test_f050_endpoint_propuesta import AJUSTES

    def fabricar(cli, **ajustes):
        monkeypatch.setattr(modulo_app, "SigridWriteClient", lambda **kw: cli)
        st = SimpleNamespace(**{**AJUSTES, "sigrid_lecturas_paralelas": 4,
                                **ajustes})
        return TestClient(modulo_app.build_app(st))
    return fabricar


# ============================ contrato (T27) ============================ #
def test_f030_r30_contrato_entrada_con_la_traza_opcional():
    from interface_adapters.api.app import IncidenciaIn

    sin = IncidenciaEntrada(id=7, recurso_ide=200, empresa=1, codigo="CIV",
                            ano=2026, mes=7, desde=5, hasta=9)
    assert (sin.hmores_ide_ini, sin.hmores_ide_fin, sin.dia_ini,
            sin.dia_fin) == (None,) * 4
    entrada = IncidenciaEntrada(**IncidenciaIn(**_json_inc(**TRAZA)).model_dump())
    assert (entrada.hmores_ide_ini, entrada.hmores_ide_fin, entrada.dia_ini,
            entrada.dia_fin) == (9001, 9002, 5, 9)
    assert IncidenciaIn(**_json_inc()).hmores_ide_ini is None


def test_f030_r30_contrato_accion_y_linea_con_los_campos_nuevos():
    a = AccionIncidencia(id=7, rol="ini", accion="editar", fecha_int=20260706)
    assert (a.fec_antes, a.hmoide) == (None, None)
    ls = LineaIncidenciaSigrid(51, 200, 20260705, "CIV", "porcentajes:inc:7:ini",
                               "PT26/1")
    assert (ls.can, ls.hmoide, ls.parte_est) == (None, None, None)


def test_f030_r46_contrato_solo_editar_publica_fec_antes():
    from interface_adapters.api.app import _con_incidencias

    editar = AccionIncidencia(id=7, rol="ini", accion="editar",
                              fecha_int=20260706, fec_antes=20260705,
                              hmores_ide=9001, hmoide=777)
    ya = AccionIncidencia(id=7, rol="fin", accion="ya_registrado",
                          fecha_int=20260709, hmores_ide=9002)
    r = _con_incidencias({}, [editar, ya])
    assert set(r["incidencias"][0]) == CLAVES_INC | {"fec_antes"}
    assert r["incidencias"][0]["fec_antes"] == 20260705
    assert set(r["incidencias"][1]) == CLAVES_INC
    assert "hmoide" not in r["incidencias"][0]          # interno


def test_f030_r30_contrato_sin_los_campos_responde_igual(api):
    peticion = {"obra": {"codigo": OBRA_ORIGEN}, "lineas": [_json_linea(1)],
                "incidencias": [_json_inc()]}
    hoy = api(ClienteInc()).post("/api/registro/preflight",
                                 json=peticion).json()
    nulos = api(ClienteInc()).post("/api/registro/preflight", json={
        **peticion, "incidencias": [_json_inc(
            hmores_ide_ini=None, hmores_ide_fin=None, dia_ini=None,
            dia_fin=None)]}).json()
    assert nulos == hoy and hoy["ok"] is True
    assert [set(x) for x in hoy["incidencias"]] == [CLAVES_INC] * 2
